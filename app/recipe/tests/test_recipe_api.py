"""Test for recipe API"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer)

RECIPES_LIST_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create an return a recipe detail URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('6.32'),
        'description': 'Sample recipe description',
        'link': 'https://example.com/recipe.pdf'
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_LIST_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user"""
        other_user = create_user(
            email='other@example.com',
            password='testpass123',
        )
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_LIST_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        self.assertEquals(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEquals(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('3.67'),
        }
        res = self.client.post(RECIPES_LIST_URL, payload)

        self.assertEquals(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for k, v in payload.items():
            self.assertEquals(getattr(recipe, k), v)

        self.assertEquals(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
        )

        payload = {'title': 'New recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        self.assertEquals(recipe.title, payload['title'])
        self.assertEquals(recipe.link, original_link)
        self.assertEquals(recipe.user, self.user)

    def test_full_update(self):
        """Test full update of a recipe"""
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe description',
        )

        payload = {
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New recipe description',
            'time_minutes': 10,
            'price': Decimal('7.57'),
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEquals(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEquals(getattr(recipe, k), v)

        self.assertEquals(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the recipe user returns an error"""
        new_user = create_user(
            email='user2@example.com',
            password='newuserpass123',
        )
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEquals(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting a recipe is successful"""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives error"""
        new_user = create_user(
            email='user2@example.com',
            password='newuserpass123',
        )
        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEquals(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title': 'Thai Praw Curry',
            'time_minutes': 30,
            'price': Decimal('5.43'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }
        res = self.client.post(RECIPES_LIST_URL, payload, format='json')
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEquals(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEquals(recipe.tags.count(), 2)

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating a recipe with existing tags"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.46'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }

        res = self.client.post(RECIPES_LIST_URL, payload, format='json')
        self.assertEquals(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEquals(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEquals(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user
            ).exists()
            self.assertTrue(exists)
