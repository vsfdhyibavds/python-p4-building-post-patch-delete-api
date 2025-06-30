import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from server.models import Review, User, Game

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed test data
            user = User(name="Test User")
            game = Game(title="Test Game", genre="Action", platform="PC", price=50)
            db.session.add_all([user, game])
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

def test_get_reviews_empty(client):
    response = client.get('/reviews')
    assert response.status_code == 200
    assert response.get_json() == []

def test_post_review(client):
    with app.app_context():
        user = User.query.first()
        game = Game.query.first()
    data = {
        'score': 8,
        'comment': 'Great game!',
        'user_id': user.id,
        'game_id': game.id
    }
    response = client.post('/reviews', data=data)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['score'] == 8
    assert json_data['comment'] == 'Great game!'
    assert json_data['user_id'] == user.id
    assert json_data['game_id'] == game.id

def test_get_review_by_id(client):
    with app.app_context():
        review = Review(score=7, comment="Nice", user_id=1, game_id=1)
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    response = client.get(f'/reviews/{review_id}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['id'] == review_id
    assert json_data['comment'] == "Nice"

def test_patch_review(client):
    with app.app_context():
        review = Review(score=5, comment="Okay", user_id=1, game_id=1)
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    patch_data = {
        'score': 9,
        'comment': 'Updated comment'
    }
    response = client.patch(f'/reviews/{review_id}', data=patch_data)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['score'] == 9
    assert json_data['comment'] == 'Updated comment'

def test_delete_review(client):
    with app.app_context():
        review = Review(score=6, comment="To be deleted", user_id=1, game_id=1)
        db.session.add(review)
        db.session.commit()
        review_id = review.id
    response = client.delete(f'/reviews/{review_id}')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['delete_successful'] is True

    # Confirm deletion
    response = client.get(f'/reviews/{review_id}')
    assert response.status_code == 404

def test_review_not_found(client):
    response = client.get('/reviews/9999')
    assert response.status_code == 404
    response = client.patch('/reviews/9999', data={'score': 10})
    assert response.status_code == 404
    response = client.delete('/reviews/9999')
    assert response.status_code == 404
