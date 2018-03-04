# test_bucketlist.py
import unittest
import os
import json
from unittest import TestCase
import unittest
import tempfile
from gabber import app, db
from gabber.projects.models import Project

class BucketlistTestCase(unittest.TestCase):
    """This class represents the bucketlist test case"""

    def setUp(self):
        # """Define test variables and initialize app."""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + "testing.db"
        app.testing = True
        self.app = app.test_client()

        with app.app_context():
            db.create_all()
        # self.project = {"title": "testing", "description": "now here", "creator": 1, "visibility": 1, "topics": ["first"] }
        # db.session.add({"title": "testing", "description": "now here", "creator": 1, "visibility": 1, "topics": ["first"]})

    def test_access_public_projects(self):
        """Test API can create a bucketlist (POST request)"""
        res = self.app.get('/api/projects/')
        print (res.data)
        print (res.status_code)
        print (res)
        print (self.project)
        # self.assertEqual(res.status_code, 201)
        # self.assertIn('Go to Borabora', str(res.data))

    def test_create_project(self):
        """Test API can create a bucketlist (POST request)"""
        res = self.app.get('/api/projects/1/sessions/')

        # res = self.app.put('/api/projects/1/', data={})
        print (res.data)
        print (res.status_code)
        print (self.project)

    def tearDown(self):
        """teardown all initialized variables."""
        print ("LOL TEAR DOWN")

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
