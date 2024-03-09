"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


from app import app, CURR_USER_KEY
import os
from unittest import TestCase

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app


app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message_logged_in(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            Message.query.filter_by(text="Hello").one()

    def test_delete_message_logged_in(self):
        """ when logged in, if user deletes their own message, tests that it is
         fully deleted from database; test redirect  """

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            u1 = User.query.get(self.u1_id)

            self.assertEqual(len(u1.messages), 0)
            self.assertEqual(resp.status_code, 200)

    # def test_add_message_logged_out(self):
    #     """ when logged out, test that user is prohibited from adding
    #     a message """

    #     with app.test_client() as c:
    #         resp = c.post("/messages/new", data={"text": "Hello"})
    #         # result = Message.query.filter_by(text="Hello").one_or_none()

    #         self.assertEqual(resp.status_code, 302)
            # self.assertIsNone(result)

    # def test_delete_message_logged_out(self):
    #     """ when logged out, check that user is prohibited from
    #       deleting messages """

    #     with app.test_client() as c:
    #         resp = c.post(
    #             f"/messages/{self.m1_id}/delete", follow_redirects=True)
    #         u1 = User.query.get(self.u1_id)

    #         self.assertEqual(len(u1.messages), 0)
    #         self.assertEqual(resp.status_code, 200)
