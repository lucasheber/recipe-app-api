"""
Test for models.
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful"""
        email = 'test@example.com'
        password = 'password'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEquals(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_mew_user_email_normalized(self):
        """Test email is normalized for new user"""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'password')
            self.assertEquals(user.email, expected)

    def test_new_without_email_raises_error(self):
        """Test that creating u user without email raises a ValueError"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'password')

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='password'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe is successful"""
        user = get_user_model().objects.create_user(
            'test4@example.com',
            'testpass123'
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample title name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description'
        )

        self.assertEqual(str(recipe), recipe.title)
