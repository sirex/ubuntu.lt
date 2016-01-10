import re
import tqdm
import datetime
import sqlalchemy as sa

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from spirit.topic.models import Topic
from spirit.comment.models import Comment
from spirit.category.models import Category
from spirit.core.utils.markdown import Markdown
from spirit.core.utils.markdown.utils.emoji import emojis
from spirit.core.utils.markdown.utils.quote import quotify

User = get_user_model()


def import_categories(metadata, conn):
    forums = sa.Table('phpbb_forums', metadata, autoload=True)

    for row in conn.execute(forums.select()):
        Category.objects.create(
            title=row.forum_name,
            description=row.forum_desc,
        )


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

        if User.objects.filter(username=row.user_username_clean).exists():
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
            username=row.user_username_clean,
            first_name=row.user_username,
            email=row.user_user_email,
            last_login=lastvisit,
            is_active=active,
            is_staff=administrator,
            is_superuser=administrator,
        )

        profile = user.st
        profile.location = row.user_user_from
        profile.last_seen = lastvisit
        profile.last_ip = row.user_user_ip
        profile.timezone = timezones.get(row.user_user_timezone, 'UTC')
        profile.is_administrator = administrator
        profile.is_moderator = moderator
        profile.is_verified = True
        profile.topic_count = conn.execute(sa.select([sa.func.count('*')], topics.c.user_id == row.user_user_id)).scalar()
        profile.comment_count = row.user_user_posts
        profile.save()


def import_topics(metadata, conn):
    users = sa.Table('phpbb_users', metadata, autoload=True)
    topics = sa.Table('phpbb_topics', metadata, autoload=True)
    forums = sa.Table('phpbb_forums', metadata, autoload=True)

    query = (
        sa.select([
            topics,
            users.c.username_clean.label('username'),
            forums.c.forum_name,
        ]).
        select_from(
            topics.
            join(users, users.c.user_id == topics.c.topic_poster).
            outerjoin(forums, topics.c.forum_id == forums.c.forum_id)
        )
    )

    total = conn.execute(
        sa.select([sa.func.count('*')], topics.c.topic_status != 2)
    ).scalar()

    for row in tqdm.tqdm(conn.execute(query), total=total):
        if row.topic_status == 2:  # topic is moved
            continue

        try:
            user = User.objects.get(username=row.username)
        except User.DoesNotExist:
            print(row.username)
            raise

        try:
            category = Category.objects.get(title=row.forum_name)
        except User.DoesNotExist:
            print(row.forum_name)
            raise

        Topic.objects.create(
            user=user,
            category=category,
            title=row.topic_title,
            date=datetime.datetime.fromtimestamp(row.topic_time),
            last_active=datetime.datetime.fromtimestamp(row.topic_last_post_time),
            is_pinned=row.topic_type == 1,
            is_globally_pinned=row.topic_type == 1,
            is_closed=row.topic_status == 1,
            is_removed=False,
            view_count=row.topic_views,
            comment_count=row.topic_replies,
        )


def bbcode_emoji(bbcode):
    emoji_map = {
        ':)': 'slight_smile',
        ':(': 'slight_frown',
        ';)': 'wink',
        ':D': 'smile',
        ':?': 'worried',
        ':P': 'stuck_out_tongue',
        '8-)': 'smiley',
        'roll': 'smirk',
        'lol': 'smile',
        'oops': 'blush',
        'shock': 'scream',
        'mrgreen': 'smiling_imp',
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


def bbcode_quote(bbcode):
    def replace(match):
        user = match.group(2)
        text = match.group(4)
        if user:
            return quotify(text, user)
        else:
            lines = text.splitlines()
            quote = "\n> ".join(lines)
            return "> %s\n" % quote
    return re.sub(r'\[quote(=&quot;(.*?)&quot;)?:([^]]+)](.*?)\[/quote:\3]', replace, bbcode, flags=re.DOTALL)


def bbcode_to_markdown(bbcode):
    bbcode = bbcode_magic_url(bbcode)
    bbcode = bbcode_emoji(bbcode)
    bbcode = bbcode_quote(bbcode)
    return bbcode


def import_topic_posts(metadata, conn, topic, topicrow):
    users = sa.Table('phpbb_users', metadata, autoload=True)
    posts = sa.Table('phpbb_posts', metadata, autoload=True)

    print(topicrow.topic_title)

    query = (
        sa.select([
            posts,
            users.c.username_clean.label('username'),
        ]).
        select_from(
            posts.
            join(users, users.c.user_id == posts.c.poster_id)
        ).
        where(posts.c.topic_id == topicrow.topic_id)
    )

    Comment.objects.filter(topic=topic).delete()

    for row in conn.execute(query):

        try:
            user = User.objects.get(username=row.username)
        except User.DoesNotExist:
            print(row.username)
            raise

        print('=' * 72)
        print(row.post_text)
        text = bbcode_to_markdown(row.post_text)
        print('-' * 72)
        print(text)

        html = Markdown().render(text)

        Comment.objects.create(
            user=user,
            topic=topic,
            comment=row.post_text,
            comment_html=html,
            date=datetime.datetime.fromtimestamp(row.post_time),
            is_modified=row.post_edit_count > 0,
            ip_address=row.poster_ip,
            modified_count=row.post_edit_count,
        )


class Command(BaseCommand):
    help = 'Import ubuntu.lt data from phpbb.'

    def handle(self, *args, **options):
        engine = sa.create_engine('mysql+pymysql://root@/ubuntult?charset=utf8')
        metadata = sa.MetaData(engine)
        conn = engine.connect()

        # import_categories(metadata, conn)
        # import_users(metadata, conn)
        # import_topics(metadata, conn)

        topics = sa.Table('phpbb_topics', metadata, autoload=True)
        title = 'Kokius Linux rinktis?'
        topic = Topic.objects.get(title=title)
        topicrow = conn.execute(
            topics.select(topics.c.topic_title == title)
        ).first()
        import_topic_posts(metadata, conn, topic, topicrow)

        self.stdout.write('it works')
