"""Tests for post router endpoints."""

from fastapi import status
from fastapi.testclient import TestClient

from models.models import AuthenticatedUser, Post


class TestPostEndpoints:
    """Test suite for post endpoints."""

    def test_get_all_posts(self, client: TestClient, test_post: Post):
        """Test getting all posts."""
        response = client.get("/posts/")
        assert response.status_code == status.HTTP_200_OK
        posts: list[Post] = response.json()
        assert isinstance(posts, list)
        assert len(posts) > 0
        assert any(p.id == test_post.id for p in posts)

    def test_get_post_by_id(self, client: TestClient, test_post: Post):
        """Test getting a specific post by ID."""
        response = client.get(f"/posts/{test_post.id}")
        assert response.status_code == status.HTTP_200_OK
        post = response.json()
        assert post["id"] == test_post.id
        assert post["content"] == test_post.content

    def test_get_post_by_invalid_id(self, client: TestClient):
        """Test getting a post with invalid ID returns 404."""
        response = client.get("/posts/99999")
        assert response.status_code == 404

    def test_get_post_with_author(
        self, client: TestClient, test_post: Post, logged_in_user: AuthenticatedUser
    ):
        """Test getting post with author information."""
        response = client.get(f"/posts/{test_post.id}/with-author")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_post.id
        assert data["content"] == test_post.content
        assert data["author_name"] == logged_in_user.user.username

    def test_create_post(self, client: TestClient, logged_in_user: AuthenticatedUser):
        """Test creating a new post."""
        if not logged_in_user.user.id:
            raise ValueError("Logged in user must have an ID")
        new_post: Post = Post(
            content="A new post created during testing.",
            author_id=logged_in_user.user.id,
        )

        response = client.post("/posts/", json=new_post)
        assert response.status_code == status.HTTP_200_OK
        data: list[Post] = response.json()
        assert data[0].content == new_post.content
        assert data[0].author_id == new_post.author_id
        assert data[0].id is not None


class TestPostLikes:
    """Test suite for post likes endpoints."""

    def test_like_post(
        self, client: TestClient, test_post: Post, logged_in_user: AuthenticatedUser
    ):
        """Test liking a post."""
        response = client.post(f"/posts/{test_post.id}/like", headers=logged_in_user.headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == logged_in_user.user.id
        assert data["post_id"] == test_post.id

    def test_like_post_unauthenticated(self, client: TestClient, test_post: Post):
        """Test that unauthenticated users cannot like posts."""
        response = client.post(f"/posts/{test_post.id}/like")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_like_nonexistent_post(self, client: TestClient, logged_in_user: AuthenticatedUser):
        """Test liking a non-existent post returns 404."""
        response = client.post("/posts/99999/like", headers=logged_in_user.headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unlike_post(
        self, client: TestClient, test_post: Post, logged_in_user: AuthenticatedUser
    ):
        """Test unliking a post."""
        client.post(f"/posts/{test_post.id}/like", headers=logged_in_user.headers)

        response = client.delete(f"/posts/{test_post.id}/like", headers=logged_in_user.headers)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unlike_post_not_liked(
        self, client: TestClient, test_post: Post, logged_in_user: AuthenticatedUser
    ):
        """Test unliking a post that wasn't liked returns 404."""
        response = client.delete(f"/posts/{test_post.id}/like", headers=logged_in_user.headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_post_likes_info(
        self, client: TestClient, test_post: Post, logged_in_user: AuthenticatedUser
    ):
        """Test getting likes information for a post."""
        client.post(f"/posts/{test_post.id}/like", headers=logged_in_user.headers)

        response = client.get(f"/posts/{test_post.id}/likes", headers=logged_in_user.headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["likes_count"] == 1
        assert data["liked_by_current_user"] is True

    def test_get_post_likes_info_not_liked(
        self, client: TestClient, test_post: Post, logged_in_user: AuthenticatedUser
    ):
        """Test getting likes info when user hasn't liked the post."""
        response = client.get(f"/posts/{test_post.id}/likes", headers=logged_in_user.headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["likes_count"] == 0
        assert data["liked_by_current_user"] is False
