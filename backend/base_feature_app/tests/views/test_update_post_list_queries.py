"""Keep update-list queries bounded as distinct shelters are added."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status

from base_feature_app.tests.factories import UpdatePostFactory

MAX_UPDATE_POST_LIST_QUERIES = 6


@pytest.mark.django_db
@pytest.mark.parametrize('post_count', [1, 20])
def test_update_post_list_stays_within_query_budget(api_client, post_count, record_property):
    """Catch a real list request exceeding the host's six-query budget."""
    posts = UpdatePostFactory.create_batch(
        post_count, shelter__owner__password=None, campaign=None, animal=None, image=None,
    )
    url = reverse('update-post-list')

    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(url)
    record_property('post_count', post_count)
    record_property('query_count', len(queries))
    record_property('distinct_shelters', len({post.shelter_id for post in posts}))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == post_count
    assert {row['id']: (row['shelter'], row['shelter_name']) for row in response.json()} == {
        post.pk: (post.shelter_id, post.shelter.name) for post in posts
    }
    assert len(queries) <= MAX_UPDATE_POST_LIST_QUERIES


@pytest.mark.django_db
def test_update_post_list_query_count_is_constant(api_client, record_property):
    """Catch an extra shelter query for every additional update post."""
    UpdatePostFactory(
        shelter__owner__password=None, campaign=None, animal=None, image=None,
    )
    url = reverse('update-post-list')

    with CaptureQueriesContext(connection) as one_post:
        small_response = api_client.get(url)
    UpdatePostFactory.create_batch(
        19, shelter__owner__password=None, campaign=None, animal=None, image=None,
    )
    with CaptureQueriesContext(connection) as twenty_posts:
        large_response = api_client.get(url)
    record_property('one_post_queries', len(one_post))
    record_property('twenty_post_queries', len(twenty_posts))
    record_property('distinct_shelters', len({row['shelter'] for row in large_response.json()}))

    assert small_response.status_code == status.HTTP_200_OK
    assert large_response.status_code == status.HTTP_200_OK
    assert len(small_response.json()) == 1
    assert len(large_response.json()) == 20
    assert len(twenty_posts) == len(one_post)
