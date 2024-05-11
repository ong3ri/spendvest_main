from flask import Flask, jsonify
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Using SQLite for simplicity
db = SQLAlchemy(app)
api = Api(app)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Add more fields as needed

class SessionResource(Resource):
    def get(self):
        sessions = Session.query.all()
        return jsonify({'sessions': [{'id': session.id, 'name': session.name} for session in sessions]})

    def post(self):
        parser = reqparse.RequestParser()
        print(f"request parser for post includes : {parser}")
        parser.add_argument('name', type=str, required=True, help='Name cannot be blank')
        args = parser.parse_args()
        print(f"sent arguments include : {args}, and type is {type(args)}")
        session_test = Session(name=args['name'])
        db.session.add(session_test)
        db.session.commit()
        return jsonify({"message":"session created succesfully", 
                        "id":f"{session_test.id}"
                        }, 201)

    def patch(self, session_id):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Name cannot be blank')
        args = parser.parse_args()
        session = Session.query.get(session_id)
        if session:
            session.name = args['name']
            db.session.commit()
            return jsonify({"message": f"Session updated successfully", "id": str(session.id)}), 200
        else:
            return jsonify({"error": "Session not found"}), 404

    def delete(self, session_id):
        session = Session.query.get(session_id)
        if session:
            db.session.delete(session)
            db.session.commit()
            return jsonify({"message": f"Session deleted successfully", "id": str(session.id)}), 200
        else:
            return jsonify({"error": "Session not found"}), 404


# Add resources to API
api.add_resource(SessionResource, '/sessions')
 

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5080)

