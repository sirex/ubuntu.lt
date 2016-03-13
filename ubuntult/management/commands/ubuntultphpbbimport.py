import re
import tqdm
import datetime
import sqlalchemy as sa
import html
import hashlib
import requests
import os.path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, is_password_usable
from django.db.models.signals import post_save
from django.conf import settings

from spirit.topic.models import Topic
from spirit.comment.models import Comment
from spirit.comment.poll.models import CommentPoll, PollMode
from spirit.comment.poll.models import CommentPollChoice
from spirit.comment.poll.models import CommentPollVote
from spirit.category.models import Category
from spirit.core.utils import mkdir_p
from spirit.core.utils.markdown import Markdown
from spirit.core.utils.markdown.utils.emoji import emojis
from spirit.user.models import UserProfile
from spirit.user.signals import update_or_create_user_profile
from spirit.category.admin.forms import CategoryForm

from ubuntult.models import PhpBBForumRefs, PhpBBTopicRefs

User = get_user_model()


def import_categories(metadata, conn):
    forums = sa.Table('phpbb_forums', metadata, autoload=True)

    Category.objects.all().delete()

    for row in conn.execute(forums.select()):
        form = CategoryForm(data={
            'parent': None,
            'title': row.forum_name,
            'description': row.forum_desc,
            'is_global': True,
            'is_closed': False,
            'is_removed': False,
        })
        category = form.save()

        PhpBBForumRefs.objects.create(
            category=category,
            phpbb_forum_id=row.forum_id,
        )

        yield row.forum_id, category


def import_users(metadata, conn):
    topics = sa.Table('phpbb_topics_posted', metadata, autoload=True)
    users = sa.Table('phpbb_users', metadata, autoload=True).alias('user')
    roles = sa.Table('phpbb_acl_roles', metadata, autoload=True).alias('role')
    bans = sa.Table('phpbb_banlist', metadata, autoload=True).alias('ban')
    acl = sa.Table('phpbb_acl_users', metadata, autoload=True).alias('acl')

    # See:
    # - forum/language/en/common.php
    # - spirit/core/utils/timezone.py
    timezones = {
        -12.00: 'Etc/GMT+12',
        -10.00: 'Etc/GMT+10',
        -9.50: 'Pacific/Marquesas',
        -8.00: 'Etc/GMT+8',
        -6.00: 'Etc/GMT+6',
        -5.00: 'Etc/GMT+5',
        -4.00: 'Etc/GMT+4',
        -2.00: 'Etc/GMT+2',
        0.00: 'Etc/GMT-2',
        1.00: 'Etc/GMT-1',
        2.00: 'Etc/GMT-2',
        3.00: 'Etc/GMT-3',
        4.00: 'Etc/GMT-4',
        5.00: 'Etc/GMT-5',
        6.00: 'Etc/GMT-6',
        6.50: 'Indian/Cocos',
        10.00: 'Etc/GMT-10',
        10.50: 'Etc/GMT-10',
        12.00: 'Etc/GMT-12',
        14.00: 'Etc/GMT-12',
    }

    user_type_map = {
        0: 'normal',
        1: 'inactive',
        2: 'ignore',
        3: 'founder',
    }

    administrator_roles = {
        'ROLE_USER_FULL',
    }

    moderator_roles = {
        'ROLE_MOD_FULL',
        'ROLE_MOD_SIMPLE',
        'ROLE_MOD_STANDARD',
    }

    query = (
        sa.select([
            users,
            roles.c.role_name,
            acl.c.forum_id,
            bans.c.ban_end,
        ], use_labels=True).
        select_from(
            users.
            outerjoin(acl, users.c.user_id == acl.c.user_id).
            outerjoin(roles, roles.c.role_id == acl.c.auth_role_id).
            outerjoin(bans, users.c.user_id == bans.c.ban_userid)
        )
    )

    total = conn.execute(
        sa.select([sa.func.count('*')]).select_from(users)
    ).scalar()

    for row in tqdm.tqdm(conn.execute(query), total=total):
        user_type = user_type_map[row.user_user_type]

        try:
            user = User.objects.get(username=row.user_username)
        except User.DoesNotExist:
            pass
        else:
            yield row.user_user_id, user
            continue

        administrator = (user_type == 'founder') or row.role_role_name in administrator_roles
        moderator = row.role_role_name in moderator_roles
        active = row.ban_ban_end is None or user_type not in ('inactive', 'ignore')

        lastvisit = datetime.datetime.fromtimestamp(row.user_user_lastvisit)

        if row.user_user_password:
            password = 'phpass%s' % row.user_user_password
        else:
            password = '!'

        user = User.objects.create(
            password=password,
            username=row.user_username,
            email=row.user_user_email,
            last_login=lastvisit,
            date_joined=datetime.datetime.fromtimestamp(row.user_user_regdate),
            is_active=active,
            is_staff=administrator,
            is_superuser=administrator,
        )

        UserProfile.objects.create(
            user=user,
            location=row.user_user_from,
            last_seen=lastvisit,
            last_ip=row.user_user_ip,
            timezone=timezones.get(row.user_user_timezone, 'UTC'),
            is_administrator=administrator,
            is_moderator=moderator,
            is_verified=True,
            topic_count=conn.execute(sa.select([sa.func.count('*')], topics.c.user_id == row.user_user_id)).scalar(),
            comment_count=row.user_user_posts,
        )

        yield row.user_user_id, user


def create_ubuntultbot_user():
    try:
        return User.objects.get(username='ubuntultbot')
    except User.DoesNotExist:
        pass

    user = User.objects.create(
        password=make_password(None),
        username='ubuntultbot',
        email='no-reply@ubuntu.lt',
        last_login=None,
        is_active=True,
        is_staff=False,
        is_superuser=False,
    )
    assert is_password_usable(user.password) is False

    UserProfile.objects.create(
        user=user,
        location='',
        last_seen=None,
        last_ip=None,
        timezone='UTC',
        is_administrator=False,
        is_moderator=False,
        is_verified=True,
        topic_count=0,
        comment_count=0,
    )

    return user


def import_topics(metadata, conn, forums, users):
    topics = sa.Table('phpbb_topics', metadata, autoload=True)

    query = sa.select([topics], topics.c.topic_status != 2)

    total = conn.execute(
        sa.select([sa.func.count('*')], topics.c.topic_status != 2)
    ).scalar()

    for row in tqdm.tqdm(conn.execute(query), total=total):
        user = users[row.topic_poster]
        category = forums[row.forum_id]
        topic = Topic.objects.create(
            user=user,
            category=category,
            title=html.unescape(row.topic_title),
            date=datetime.datetime.fromtimestamp(row.topic_time),
            last_active=datetime.datetime.fromtimestamp(row.topic_last_post_time),
            is_pinned=row.topic_type == 1,
            is_globally_pinned=row.topic_type == 1,
            is_closed=row.topic_status == 1,
            is_removed=False,
            view_count=row.topic_views,
            comment_count=row.topic_replies,
        )

        PhpBBTopicRefs.objects.create(
            topic=topic,
            phpbb_forum_id=row.forum_id,
            phpbb_topic_id=row.topic_id,
        )

        yield row, topic


def bbcode_emoji(bbcode):
    emoji_map = {
        ':)': 'slight_smile',
        ':|': 'neutral_face',
        ':(': 'slight_frown',
        ';)': 'wink',
        ':D': 'smile',
        ':?': 'worried',
        ':P': 'stuck_out_tongue',
        ':-?': 'yum',
        ';-)': 'wink',
        ':-)': 'smiley',
        ':-D': 'smile',
        ':-(': 'slight_frown',
        '8-)': 'smiley',
        ':-|': 'neutral_face',
        ':!:': 'exclamation',
        ':?:': 'question',
        'roll': 'smirk',
        'lol': 'smile',
        'oops': 'blush',
        'shock': 'astonished',
        'mrgreen': 'smiley_cat',
        'twisted': 'smiling_imp',
        'evil': 'imp',
        'geek': 'relieved',
        'ugeek': 'sunglasses',
        'arrow': 'point_right',
        'idea': 'bulb',
    }

    def replace(match):
        emoji = match.group(1)
        emoji = emoji_map.get(emoji, emoji)
        emoji = emoji.strip(':')
        emoji = emoji_map.get(emoji, emoji)
        assert emoji in emojis, emoji
        return ':%s:' % emoji

    return re.sub(r'<!-- s([^ ]+) --><img src="[^"]+" alt="[^"]*" title="[^"]*" /><!-- s\1 -->', replace, bbcode)


def bbcode_magic_url(bbcode):
    def replace(match):
        url = match.group(2)
        text = match.group(3)
        if url == text:
            return url
        else:
            return '[%s](%s)' % (text, url)
    return re.sub(r'<!-- ([lmwe]) --><a.*? href="([^"]+)">(.*?)</a><!-- \1 -->', replace, bbcode)


class Context(object):

    def __init__(self, env, code, name, text, params=None):
        self.env = env
        self.code = code
        self.name = name
        self.text = text
        self.params = params

    def render_quote(self):
        lines = self.text.strip().splitlines()
        quote = "\n> ".join(lines)
        if self.params:
            if self.params.startswith('=&quot;') and self.params.endswith('&quot;'):
                user = self.params[7:-6]
            else:
                user = self.params.strip()
            return '> @%s rašė:\n> %s\n' % (user, quote)
        else:
            return "> %s\n" % quote

    def render_code(self):
        lang = ''
        if self.params and self.params.startswith('='):
            lang = self.params[1:]
        return '```%s\n%s\n```' % (lang, self.text.strip())

    def render_url(self):
        if self.params:
            if self.params.startswith('='):
                url = self.params[1:]
            else:
                url = self.params
            return '[%s](%s)' % (self.text, url)
        else:
            return self.text

    def render_youtube(self):
        return self.text

    def render_img(self):
        if self.params:
            if self.params.startswith('='):
                url = self.params[1:]
            else:
                url = self.params
            return '![%s](%s)' % (self.text, url)
        else:
            return '![](%s)' % self.text

    def _upload_file(self, name, url):
        resp = requests.get(url)
        file_hash = hashlib.md5(resp.content).hexdigest()
        hashed_name = '%s%s' % (file_hash, os.path.splitext(name)[1].lower())
        upload_to = os.path.join('spirit', 'images', str(self.env.users[self.env.postrow.poster_id].pk))
        uploaded_url = os.path.join(settings.MEDIA_URL, upload_to, hashed_name)
        media_path = os.path.join(settings.MEDIA_ROOT, upload_to)
        mkdir_p(media_path)
        with open(os.path.join(media_path, hashed_name), 'wb') as f:
            f.write(resp.content)
        return uploaded_url

    def render_attachment(self):
        attachments = self.env.tables['attachments']

        assert self.params.startswith('='), repr(self.params)
        param = int(self.params[1:])

        row = self.env.conn.execute(
            attachments.select(sa.and_(
                attachments.c.post_msg_id == self.env.postrow.post_id,
                attachments.c.in_message == param,
            ))
        ).first()

        if row is None:
            # print('attachment error: post_msg_id = %s and in_message = %s\n%s' % (self.env.postrow.post_id, param, self.text))
            return ''

        url = 'https://ubuntu.lt/forum/download/file.php?id=%s' % row.attach_id
        url = self._upload_file(row.real_filename, url)

        if row.mimetype.startswith('image/'):
            return '![%s](%s)' % (row.real_filename, url)
        else:
            return '[%s](%s)' % (row.real_filename, url)

    def render_list(self):
        text = re.sub(r'\[/\*(:[^]]+)?]', '', self.text)
        return re.sub(r'^\s*\[\*(:[^]]+)?]', '*', text, flags=re.MULTILINE)

    def render_size(self):
        return '**%s**' % self.text if '\n' not in self.text else self.text

    def render_color(self):
        return '**%s**' % self.text if '\n' not in self.text else self.text

    def render_b(self):
        return '**%s**' % self.text if '\n' not in self.text else self.text

    def render_i(self):
        return '*%s*' % self.text if '\n' not in self.text else self.text

    def render_u(self):
        return '*%s*' % self.text if '\n' not in self.text else self.text

    def render_s(self):
        return '~~%s~~' % self.text if '\n' not in self.text else self.text

    def render_email(self):
        return self.text


def iterbbtags(bbcode):
    pos = 0
    for match in re.finditer(r'\[/?([a-z]+)([^]]*)(:[a-z0-9]+)]', bbcode):
        yield bbcode[pos:match.start()], match
        pos = match.end()
    yield bbcode[pos:], None


def bbcode_tags(env, bbcode):
    bbtags = (
        'quote', 'code', 'url', 'youtube', 'img', 'attachment', 'list', 'size', 'color', 'b', 'i', 'u', 's', 'email',
    )
    stack = [Context(env, None, None, '')]
    for text, match in iterbbtags(bbcode):
        stack[-1].text += text
        if match is None:
            continue
        tag = match.group(0)
        name = match.group(1)
        params = match.group(2)
        if params == '\\':
            stack[-1].text += tag
            continue
        if name not in bbtags:
            stack[-1].text += tag
            continue
        if tag == '[/%s]' % stack[-1].code:
            node = stack.pop()
            render = getattr(node, 'render_%s' % node.name)
            stack[-1].text += render()
        else:
            code = match.group(1) + (match.group(3) or '')
            stack.append(Context(env, code, name, '', params))
    while len(stack) > 1:
        node = stack.pop()
        render = getattr(node, 'render_%s' % node.name)
        stack[-1].text += render()
    return stack[-1].text


def bbcode_to_markdown(env, bbcode):
    bbcode = bbcode_tags(env, bbcode)
    bbcode = bbcode_magic_url(bbcode)
    bbcode = bbcode_emoji(bbcode)
    bbcode = html.unescape(bbcode)
    return bbcode


class Env(object):
    def __init__(self, metadata, conn):
        self.metadata = metadata
        self.conn = conn
        self.topic = None
        self.topicrow = None
        self.postrow = None
        self.users = None

        self.tables = {
            'attachments': sa.Table('phpbb_attachments', metadata, autoload=True),
        }


def import_topic_polls(metadata, conn, users, topic, topicrow):
    poll = sa.Table('phpbb_poll_options', metadata, autoload=True)
    votes = sa.Table('phpbb_poll_votes', metadata, autoload=True)

    query = sa.select([poll], poll.c.topic_id == topicrow.topic_id)

    options = []
    for row in conn.execute(query):
        options.append({
            'id': row.poll_option_id,
            'text': row.poll_option_text,
            'total': row.poll_option_total,
        })

    if options:
        text = '\n'.join(['%d. %s' % (i, x['text']) for i, x in enumerate(options, 1)])
        text = '\n'.join([
            '[poll name=1 min=1 max=%d close=%dd]' % (topicrow.poll_max_options, (topicrow.poll_length or 7)),
            '# %s' % topicrow.poll_title,
            text,
            '[/poll]',
        ])

        user = users[topicrow.topic_poster]

        markdown = Markdown()
        html = markdown.render(text)  # noqa

        comment = Comment.objects.create(
            user=user,
            topic=topic,
            comment=text,
            comment_html=html,
            date=datetime.datetime.fromtimestamp(topicrow.topic_time) - datetime.timedelta(seconds=1),
            is_modified=0,
            ip_address=None,
            modified_count=0,
        )

        instance = CommentPoll.objects.create(
            comment=comment,
            name='1',
            title=topicrow.poll_title,
            mode=PollMode.DEFAULT,
            choice_min=1,
            choice_max=topicrow.poll_max_options,
            close_at=comment.date + datetime.timedelta(days=(topicrow.poll_length or 7)),
            created_at=comment.date,
        )

        choices = {}
        for i, option in enumerate(options, 1):
            choice = CommentPollChoice.objects.create(
                poll=instance,
                number=i,
                description=option['text'],
                vote_count=option['total'],
            )
            choices[option['id']] = choice

        query = sa.select([votes], sa.and_(
            votes.c.topic_id == topicrow.topic_id,
            votes.c.poll_option_id.in_([x['id'] for x in options])
        ))
        for i, row in enumerate(conn.execute(query), 1):
            CommentPollVote.objects.create(
                voter=users[row.vote_user_id],
                choice=choices[row.poll_option_id],
                created_at=datetime.datetime.fromtimestamp(topicrow.topic_time) + datetime.timedelta(seconds=i),
            )


def import_topic_posts(metadata, conn, users, topic, topicrow):
    env = Env(metadata, conn)
    env.topic = topic
    env.topicrow = topicrow
    env.users = users

    posts = sa.Table('phpbb_posts', metadata, autoload=True)

    query = sa.select([posts], posts.c.topic_id == topicrow.topic_id)

    import_topic_polls(metadata, conn, users, topic, topicrow)

    for row in conn.execute(query):
        env.postrow = row
        user = users[row.poster_id]
        text = None

        try:
            text = bbcode_to_markdown(env, row.post_text)
            html = Markdown().render(text)  # noqa
        except Exception:
            import pprint
            pprint.pprint(dict(topicrow))
            pprint.pprint(dict(row))
            print('=' * 72)
            print(row.post_text)
            print('-' * 72)
            print(text)
            raise

        Comment.objects.create(
            user=user,
            topic=topic,
            comment=text,
            comment_html=html,
            date=datetime.datetime.fromtimestamp(row.post_time),
            is_modified=row.post_edit_count > 0,
            ip_address=row.poster_ip,
            modified_count=row.post_edit_count,
        )

    text = '\n'.join([
        'Tema perkelta iš https://legacy.ubuntu.lt/forum/viewtopic.php?f={forum_id}&t={topic_id}'
    ]).format(forum_id=topicrow.forum_id, topic_id=topicrow.topic_id)
    html = Markdown().render(text)  # noqa
    Comment.objects.create(
        user=users['bot'],
        topic=topic,
        comment=text,
        comment_html=html,
        date=datetime.datetime.now(),
        is_modified=False,
        ip_address=None,
        modified_count=0,
    )


class Command(BaseCommand):
    help = 'Import ubuntu.lt data from phpbb.'

    def handle(self, *args, **options):
        self.stdout.write('importing ubuntu.lt phpbb forum data')
        post_save.disconnect(update_or_create_user_profile, sender=User, dispatch_uid='spirit.user.signals')

        self.stdout.write('connecting to database...')
        engine = sa.create_engine('mysql+pymysql://root@/ubuntult?charset=utf8')
        metadata = sa.MetaData(engine)
        conn = engine.connect()

        topics = sa.Table('phpbb_topics', metadata, autoload=True)

        PhpBBTopicRefs.objects.all().delete()
        CommentPollVote.objects.all().delete()

        self.stdout.write('importing categories...')
        forums = dict(import_categories(metadata, conn))
        self.stdout.write('importing users...')
        users = dict(import_users(metadata, conn))
        users['bot'] = create_ubuntultbot_user()

        self.stdout.write('importing topics...')
        total = conn.execute(
            sa.select([sa.func.count('*')], topics.c.topic_status != 2).select_from(topics)
        ).scalar()

        for topicrow, topic in tqdm.tqdm(import_topics(metadata, conn, forums, users), total=total):
            import_topic_posts(metadata, conn, users, topic, topicrow)

        self.stdout.write('done.')
