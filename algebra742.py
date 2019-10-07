import os
from flask import Flask, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import select, and_
from flask.ext.wtf import Form
from wtforms import TextField, IntegerField, BooleanField, FieldList, StringField, RadioField
from random import randint
import markdown
from markdown_include.include import MarkdownInclude

from pylti.flask import lti
from functools import wraps
from flask import request, render_template
from flask import Response, make_response, after_this_request
from functools import wraps

VERSION = '0.0.1'
app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    lti_user_id = db.Column(db.String(255), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

from datetime import datetime

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment = db.Column(db.String(255))
    number = db.Column(db.Integer)

question_scores = db.Table('question_scores',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id')),
    db.Column('score', db.Float),
    db.Column('datetime', db.DateTime, nullable=False,
        default=datetime.utcnow)
)
# FIXME: Unique constraint?

#def AnswerChecker():

EPQuestionData = [
        {
            'Type': 'MC',
            'Question': 'Is the left hand side of the following expression a sum or a product? $3x+2=8$',
            'Choices': [('a', 'Sum'),('b', 'Product')]
            },
        {
            'Type': 'MC',
            'Question': 'Which property is represented in the following solution?',
            'a': '',
            'b': '',
            'c': '',
            'd': '',
            },
        {
            'Type': 'Numerical',
            'Question': 'Evaluate $-5-(-2)$',
            },
        ]
BalanceQuestionData = [
        {
            'LHSImage': 'BalanceImages/IMG_1634.jpg',
            'RHSImage': 'BalanceImages/IMG_1635.jpg',
            'LHS': 'a',
            'RHS': '2*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of an orange cube', 'the weight of a small paper clip'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1632.jpg',
            'RHSImage': 'BalanceImages/IMG_1633.jpg',
            'LHS': '2*a',
            'RHS': '4*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of an orange cube', 'the weight of a small paper clip'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1630.jpg',
            'RHSImage': 'BalanceImages/IMG_1631.jpg',
            'LHS': '3*a',
            'RHS': '6*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of an orange cube', 'the weight of a small paper clip'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1627.jpg',
            'RHSImage': 'BalanceImages/IMG_1628.jpg',
            'LHS': '4*a+b',
            'RHS': '9*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of an orange cube', 'the weight of a small paper clip'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1621.jpg',
            'RHSImage': 'BalanceImages/IMG_1622.jpg',
            'LHS': '3*a',
            'RHS': '6*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of a nickel', 'the weight of a penny'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1619.jpg',
            'RHSImage': 'BalanceImages/IMG_1620.jpg',
            'LHS': '3*a+b',
            'RHS': '7*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of a nickel', 'the weight of a penny'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1612.jpg',
            'RHSImage': 'BalanceImages/IMG_1613.jpg',
            'LHS': '2*a+3*b',
            'RHS': '13*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of an S-hook', 'the weight of a pencil tip eraser'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1604.jpg',
            'RHSImage': 'BalanceImages/IMG_1605.jpg',
            'LHS': '2*a+b',
            'RHS': '15*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of an eraser', 'the weight of a yellow block'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1594.jpg',
            'RHSImage': 'BalanceImages/IMG_1595.jpg',
            'LHS': '3*a+2*b',
            'RHS': '5*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of a clip', 'the weight of a hex nut'] 
            },
        {
            'LHSImage': 'BalanceImages/IMG_1576.jpg',
            'RHSImage': 'BalanceImages/IMG_1577.jpg',
            'LHS': '2*a+b',
            'RHS': '5*b',
            'Variables': ['a', 'b'],
            'Quantities': ['the weight of a hex nut', 'the weight of a dime'] 
            },
        ]

#class Assignment(db.Model):
#    id = db.Column(db.Integer, primary_key=True)
#    description = db.Column(db.String(80), nullable=False)
#    body = db.Column(db.Text, nullable=False)
#    pub_date = db.Column(db.DateTime, nullable=False,
#        default=datetime.utcnow)
#
#    category_id = db.Column(db.Integer, db.ForeignKey('category.id'),
#        nullable=False)
#    category = db.relationship('Category',
#        backref=db.backref('posts', lazy=True))
#
#    def __repr__(self):
#        return '<Post %r>' % self.title
#


def returns_html(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        r = f(*args, **kwargs)
        r = make_response(r)
        r.headers['Content-type'] = 'text/html; charset=utf-8'
        return r
    return decorated_function

def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator

class AddForm(Form):
    """ Add data from Form

    :param Form:
    """

    p1 = IntegerField('p1')
    p2 = IntegerField('p2')
    result = IntegerField('result')
    correct = BooleanField('correct')

class MCForm(Form):
    """ Add data from Form

    :param Form:
    """
    options = RadioField(u'Choices')

class NumericAnswerForm(Form):
    """ Add data from Form

    :param Form:
    """
    answer = FieldList(StringField('answer'))
    
class EquationForm(Form):
    """ Add data from Form

    :param Form:
    """
    variables = FieldList(StringField('variable'))
    lhs = TextField('lhs')
    rhs = TextField('rhs')
    
class UserInfoForm(Form):
    """ Add data from Form

    :param Form:
    """
    username = StringField('username')
    password = StringField('password')


def error(exception=None):
    """ render error page

    :param exception: optional exception
    :return: the error.html template rendered
    """
    return render_template('error.html')

def get_or_create(session, model, defaults=None, **kwargs):
    from sqlalchemy.sql.expression import ClauseElement
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        session.add(instance)
        return instance

@app.route('/EPAssessment/<q>', methods=['GET', 'POST'])
@app.route('/EPAssessment/', methods=['GET', 'POST'])
@templated('MarkdownQuestionGeneral.html')
#@lti(request='session', error=error, app=app)
#def EPAssessment(lti=lti, q=None):
def EPAssessment(q=None):
    #user = db.session.query(User).filter_by(lti_user_id=lti.name).first()
    user = User(username="test user", lti_user_id="asdf")
    if q is None:
        for i in range(len(EPQuestionData)):
            statement = select([question_scores,Question.__table__]).where(and_(question_scores.c.user_id==user.id, question_scores.c.question_id==Question.__table__.c.id, Question.__table__.c.number==i+1, question_scores.c.score==1))
            results = db.session.execute(statement).first()
            if not results:
                q = i+1
                break
    if not user:
        form = UserInfoForm()
        return render_template('GetUserInfo.html', lti=lti, form=form)
    q = int(q)
    @after_this_request
    def add_header(response):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    from sympy import simplify, symbols
    from sympy.parsing.sympy_parser import parse_expr
    from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
    transformations = (standard_transformations + (implicit_multiplication_application,))
    assignment = 'EPAssessment'
    a,b = symbols("a b")
#    markdown_include = MarkdownInclude(
#                           configs={'base_path':app.config['MARKDOWN_INCLUDE_PATH']}
#                           )
#    md = markdown.Markdown(extensions=['mdx_math','attr_list','markdown.extensions.extra','markdown.extensions.meta',markdown_include])
#    with open(os.path.join(app.config['RESOURCES_DIR'],'RepresentBalances', 'Question{:d}.md'.format(q)), 'rb') as f:
#        source = f.read()
#    result = md.convert(source.decode('utf-8'))
#    try:
#        title = md.Meta['title'][0]
#    except:
#        title = 'untitled'
    if EPQuestionData[q-1]['Type'] == 'MC':
        form = MCForm()
        form.choices = EPQuestionData[q-1]['Choices']
        # Check answers
        # Answers array
        correct = False
        if request.method == 'POST':
            question = get_or_create(db.session, Question, assignment=assignment, number=q)
            db.session.commit()
            statement = question_scores.insert().values(user_id=user.id, question_id=question.id, score=bool(correct))
            db.session.execute(statement)
            db.session.commit()
        if len(EPQuestionData) > q+1:
            NextQuestion = q+1
        else:
            NextQuestion = None
    return dict(title='Assessment on Rational Numbers, Properties of Equality', content='', form=form, q=q, NextQuestion=NextQuestion, correct=correct, QuestionData=EPQuestionData[q-1])

@app.route('/RepresentBalances/<q>', methods=['GET', 'POST'])
@app.route('/RepresentBalances/', methods=['GET', 'POST'])
@templated('MarkdownQuestion.html')
@lti(request='session', error=error, app=app)
def RepresentBalances(lti=lti, q=None):
    user = db.session.query(User).filter_by(lti_user_id=lti.name).first()
    if q is None:
        for i in range(len(BalanceQuestionData)):
            statement = select([question_scores,Question.__table__]).where(and_(question_scores.c.user_id==user.id, question_scores.c.question_id==Question.__table__.c.id, Question.__table__.c.number==i+1, question_scores.c.score==1))
            results = db.session.execute(statement).first()
            if not results:
                q = i+1
                break
    if not user:
        form = UserInfoForm()
        return render_template('GetUserInfo.html', lti=lti, form=form)
    if q == 'submit':
        lti.post_grade(1)
        return render_template('grade.html', form=form)
    q = int(q)
    @after_this_request
    def add_header(response):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    from sympy import simplify, symbols
    from sympy.parsing.sympy_parser import parse_expr
    from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
    transformations = (standard_transformations + (implicit_multiplication_application,))
    assignment = 'RepresentBalances'
    a,b = symbols("a b")
#    markdown_include = MarkdownInclude(
#                           configs={'base_path':app.config['MARKDOWN_INCLUDE_PATH']}
#                           )
#    md = markdown.Markdown(extensions=['mdx_math','attr_list','markdown.extensions.extra','markdown.extensions.meta',markdown_include])
#    with open(os.path.join(app.config['RESOURCES_DIR'],'RepresentBalances', 'Question{:d}.md'.format(q)), 'rb') as f:
#        source = f.read()
#    result = md.convert(source.decode('utf-8'))
#    try:
#        title = md.Meta['title'][0]
#    except:
#        title = 'untitled'
    form = EquationForm()
    n = len(BalanceQuestionData[q-1]['Variables'])
    for i in range(n):
        form.variables.append_entry()
    # Check answers
    # Answers array
    try:
        lhs_input = parse_expr(form.lhs.data, transformations=transformations)
        rhs_input = parse_expr(form.rhs.data, transformations=transformations)
        lhs = BalanceQuestionData[q-1]['LHS']
        rhs = BalanceQuestionData[q-1]['RHS']
        for i,variable in enumerate(BalanceQuestionData[q-1]['Variables']):
            lhs = lhs.replace(variable, form.variables[i].data)
            rhs = rhs.replace(variable, form.variables[i].data)
        lhs = parse_expr(lhs, transformations=transformations)
        rhs = parse_expr(rhs, transformations=transformations)
        correct = simplify(lhs-lhs_input) == 0 and simplify(rhs-rhs_input) == 0
    except:
        lhs = form.lhs.data
        rhs = form.rhs.data
        correct = False
    if request.method == 'POST':
        question = get_or_create(db.session, Question, assignment=assignment, number=q)
        db.session.commit()
        statement = question_scores.insert().values(user_id=user.id, question_id=question.id, score=bool(correct))
        db.session.execute(statement)
        db.session.commit()
    if len(BalanceQuestionData) > q+1:
        NextQuestion = q+1
    else:
        NextQuestion = None
    return dict(title='Representing balance scales', content='', form=form, q=q, NextQuestion=NextQuestion, lhs=lhs, rhs=rhs, correct=correct, QuestionData=BalanceQuestionData[q-1])

@app.route('/markdown/<filename>')
@templated('markdown.html')
def markdown_view(lti=lti, filename=None):
    @after_this_request
    def add_header(response):
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    markdown_include = MarkdownInclude(
                           configs={'base_path':app.config['MARKDOWN_INCLUDE_PATH']}
                           )
    md = markdown.Markdown(extensions=['mdx_math','attr_list','markdown.extensions.extra','markdown.extensions.meta',markdown_include])
    with open(os.path.join(app.config['RESOURCES_DIR'],filename), 'rb') as f:
        source = f.read()
    result = md.convert(source.decode('utf-8'))
    try:
        title = md.Meta['title'][0]
    except:
        title = 'untitled'
    return dict(title=title, content=result)

@app.route('/is_up', methods=['GET'])
def hello_world(lti=lti):
    """ Indicate the app is working. Provided for debugging purposes.

    :param lti: the `lti` object from `pylti`
    :return: simple page that indicates the request was processed by the lti
        provider
    """
    return render_template('up.html', lti=lti)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET'])
@app.route('/lti/', methods=['GET', 'POST'])
@lti(request='initial', error=error, app=app)
def index(lti=lti):
    """ initial access page to the lti provider.  This page provides
    authorization for the user.

    :param lti: the `lti` object from `pylti`
    :return: index page for lti provider
    """
    user = db.session.query(User).filter_by(lti_user_id=lti.name).first()
    if user:
        return render_template('index.html', user=user)
    else:
        form = UserInfoForm()
        return render_template('GetUserInfo.html', lti=lti, form=form)


@app.route('/userinfo', methods=['GET','POST'])
@lti(request='session', error=error, app=app)
def SetUserInfo(lti=lti):
    from sqlalchemy.sql.expression import ClauseElement
    user = db.session.query(User).filter_by(lti_user_id=lti.name).first()
    if user:
        user.username = form.username.data
    else:
        form = UserInfoForm()
        user = User(lti_user_id=lti.name, username=form.username.data)
        db.session.add(user)
    db.session.commit()
    return render_template('index.html', user=user)


@app.route('/index_staff', methods=['GET', 'POST'])
@lti(request='session', error=error, role='staff', app=app)
def index_staff(lti=lti):
    """ render the contents of the staff.html template

    :param lti: the `lti` object from `pylti`
    :return: the staff.html template rendered
    """
    return render_template('staff.html', lti=lti)


@app.route('/add', methods=['GET'])
@lti(request='session', error=error, app=app)
def add_form(lti=lti):
    """ initial access page for lti consumer

    :param lti: the `lti` object from `pylti`
    :return: index page for lti provider
    """
    form = AddForm()
    form.p1.data = randint(1, 9)
    form.p2.data = randint(1, 9)
    return render_template('add.html', form=form)


@app.route('/grade', methods=['POST'])
@lti(request='session', error=error, app=app)
def grade(lti=lti):
    """ post grade

    :param lti: the `lti` object from `pylti`
    :return: grade rendered by grade.html template
    """
    form = AddForm()
    correct = ((form.p1.data + form.p2.data) == form.result.data)
    form.correct.data = correct
    lti.post_grade(1 if correct else 0)
    return render_template('grade.html', form=form)


def set_debugging():
    """ enable debug logging

    """
    import logging
    import sys

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(name)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)

set_debugging()

if __name__ == '__main__':
    """
    For if you want to run the flask development server
    directly
    """
    port = int(os.environ.get("FLASK_LTI_PORT", 5000))
    host = os.environ.get("FLASK_LTI_HOST", "localhost")
    app.run(debug=True, host=host, port=port)
