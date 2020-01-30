# Copyright (C) 2020 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import twitter

from django.conf import settings
from scorebot.utils.logger import log_warning, log_debug
from scorebot.utils.constants import CONST_GAME_GAME_MESSAGE


class EventHost(object):
    def __init__(self):
        self.games = dict()
        try:
            self.twitter = twitter.Api(
                consumer_key=settings.TWITTER_API["CONSUMER_KEY"],
                consumer_secret=settings.TWITTER_API["CONSUMER_SECRET"],
                access_token_key=settings.TWITTER_API["ACCESS_TOKEN"],
                access_token_secret=settings.TWITTER_API["ACCESS_TOKEN_SECRET"],
            )
        except twitter.TwitterError:
            log_warning(
                "EVENT",
                "Error authenticating the Twitter API! Posts will be unavailable!",
            )
            self.twitter = None

    def post_tweet(self, status):
        if not settings.TWITTER_API["ENABLED"]:
            log_debug("EVENT-TWITTER", 'Twitter not enabled.  Post: "%s"' % status)
            return
        if self.twitter is None:
            log_warning(
                "EVENT", "Twitter API in not available! Posts will be unavailable!"
            )
            return
        try:
            self.twitter.PostUpdate(
                "%s %s" % (status, " ".join(settings.TWITTER_API["HASHTAGS"]))
            )
        except twitter.TwitterError as twitterError:
            if "Status is a duplicate" in str(twitterError.message):
                log_debug("EVENT", 'Posted a duplicate status! "%s"' % status)
            else:
                self.twitter = None


EVENT_HOST = EventHost()


def post_tweet(tweet_message):
    EVENT_HOST.post_tweet(tweet_message)


def get_scoreboard_message(game_id):
    if game_id in EVENT_HOST.games:
        return EVENT_HOST.games[game_id]
    return CONST_GAME_GAME_MESSAGE
