import os
from flask import Flask, request, abort, jsonify
from flask.cli import AppGroup
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# paginate question helper method
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    # CORS Header
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,true")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS,PATCH")
        return response


    @app.route('/categories', methods=['GET'])
    def get_categories():
        allCategories = Category.query.order_by(Category.id).all()

        all_categories = {category.id: category.type for category in allCategories}

        return jsonify(
            {
            'success': True,
            'categories': all_categories
            }
        )

    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """


    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        # if nothing is return abort
        if len(current_questions) == 0:
            abort(404)

        allCategories = Category.query.order_by(Category.id).all()
        all_categories = {category.id: category.type for category in allCategories}

        return jsonify({
            'success': True,
            'categories': all_categories,
            'questions': current_questions,
            'totalQuestions': len(Question.query.all())
        })
            

    # handler for POST and GET requests to the /questions endpoint
    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()
        searchTerm = body.get('searchTerm')
             
        
        try:
            # search questions
            if searchTerm:
                # get matching questions from the database
                selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(searchTerm)))

                current_questions = paginate_questions(request, selection)

                allCategories = Category.query.order_by(Category.id).all()
                all_categories = {category.id: category.type for category in allCategories}
                return jsonify({
                    'categories': all_categories,
                    'questions': current_questions,
                    'totalQuestions': len(Question.query.all())
                })

            #for creating new questions
            else:
                question = body.get('question')
                answer = body.get('answer')
                difficulty = int(body.get('difficulty'))
                category = int(body.get('category'))

                if ((question is None) or (answer is None) or (difficulty is None) or (category is None)):
                    abort(422)

                questions = Question(
                question=question,
                answer = answer,
                difficulty =difficulty,
                category =category
                )
                questions.insert()
                return jsonify({'success': True})
        
        except:
            abort(422)

        
        

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        allQuestions = Question.query.filter(Question.category == category_id).all()
        category = Category.query.filter(Category.id == category_id).one_or_none()

        # if not question is returned for that category then abort with a 404 error
        if allQuestions is None:
            abort(404)
        questions = [question.format() for question in allQuestions]
        
        return jsonify({
            'success': True,
            'questions': questions,
            'totalQuestions' : len(allQuestions),
            'currentCategory' : category.type

        })



    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter(Question.id == question_id).one_or_none()
        if question is None:
            abort(404)
        

        question.delete()
        return jsonify({
            'success': True,
            'deleted': question_id,
            'total_question': len(Question.query.all())
        })


    @app.route('/quizzes', methods=['POST'])
    def quiz():
        try:
            # get request body
            body = request.get_json()

            # if the required parameters exist in the request body we proceed, else we abort
            if ('quiz_category' in body and 'previous_questions' in body):
                category = body.get('quiz_category', None)
                previous_questions = body.get('previous_questions', None)
                
                # if category is provided then use that to query else query all questions
                if (category['id']):
                    available_questions =  Question.query.filter_by(category=category['id']).filter(Question.id.notin_((previous_questions))).all()
                else:
                    available_questions = Question.query.filter(Question.id.notin_((previous_questions))).all()

                # generate a random question from the list of available questions returned above
                if len(available_questions) > 0:
                    new_question =  available_questions[random.randrange(0, len(available_questions))].format()
                    return jsonify({
                    'success': True,
                    'question': new_question
                    })

                # return none if nothing was available questions is empty
                else:
                    return jsonify({
                        'success': True,
                        'question': None
                    })

            else:
                abort(422)
        except:
            abort(422)

    # error handling for the expected errors
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'cannot be processed'
        }), 422

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    return app

