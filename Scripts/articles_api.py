import flask
from flask import request, jsonify
# import mysql.connector as mysql
from flask_mysqldb import MySQL

app = flask.Flask(__name__)
app.config["DEBUG"] = True

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'articlesdb'

mysql = MySQL(app)

# def create_db_con():
#     db_con = mysql.connect(host="localhost", user="root",
#                            passwd="root", db="dba", auth_plugin='mysql_native_password')

#     return db_con


books = [
    {'id': 0,
     'title': 'A Fire Upon the Deep',
     'author': 'Vernor Vinge',
     'first_sentence': 'The coldsleep itself was dreamless.',
     'year_published': '1992'},
    {'id': 1,
     'title': 'The Ones Who Walk Away From Omelas',
     'author': 'Ursula K. Le Guin',
     'first_sentence': 'With a clamor of bells that set the swallows soaring, the Festival of Summer came to the city Omelas, bright-towered by the sea.',
     'published': '1973'},
    {'id': 2,
     'title': 'Dhalgren',
     'author': 'Samuel R. Delany',
     'first_sentence': 'to wound the autumnal city.',
     'published': '1975'}
]


@app.route('/', methods=['GET'])
def home():
    return """<h1>Interoperabilidade Semântica TP API</h1>
              <p> Gabriel Santos PG41076 </p>"""


@app.route('/api/books/all', methods=['GET'])
def all_books():
    return jsonify(books)


@app.route('/api/authors', methods=['GET'])
def get_authors():
    # db_con = create_db_con()
    cur = mysql.connection.cursor()
    query_string = request.args
    query = 'SELECT * FROM AUTHOR WHERE'
    filter = []

    if 'orcid_id' in query_string:
        query += ' orcid_id = %s'
        filter.append(query_string['orcid_id'])
        print(filter)
        cur.execute(query, filter)
    elif len(query_string) == 0:
        query = query[:-4]
        cur.execute(query)
    else:
        return page_not_found(404)
    # columns = [x[0] for x in cur.description]

    columns = list(map(lambda x: x[0], cur.description))
    results = [dict(zip(columns, x)) for x in cur.fetchall()]
    cur.close()
    return jsonify(results)


@app.route('/api/works', methods=['GET'])
def get_articles():
    # db_con = create_db_con()
    cur = mysql.connection.cursor()
    query_string = request.args
    query = 'SELECT * FROM WORK WHERE'
    filter = []

    if 'from' in query_string:
        get_orcid_cur = mysql.connection.cursor()
        get_orcid_cur.execute(
            'SELECT work_id FROM Author_Work aw INNER JOIN Author a on aw.author_id = a.author_id WHERE a.orcid_id = %s', [query_string['from']])
        work_ids = get_orcid_cur.fetchall()
        work_ids = tuple([x[0] for x in work_ids])

        get_orcid_cur.close()
        cur.execute('SELECT * FROM Work WHERE work_id IN %s ', [work_ids])
    elif 'work_id' in query_string:
        query += ' work_id = %s'
        filter.append(query_string['work_id'])
        cur.execute(query, filter)

    elif len(query_string) == 0:
        query = query[:-4]
        cur.execute(query)
    else:
        return page_not_found(404)

    columns = list(map(lambda x: x[0], cur.description))
    results = [dict(zip(columns, x)) for x in cur.fetchall()]
    cur.close()
    return jsonify(results)


@app.route('/api/scopus', methods=['GET'])
def get_scopus():
    cur = mysql.connection.cursor()
    query_string = request.args
    query = 'SELECT * FROM SCOPUS_INFO WHERE'
    filter = []

    if 'scopus_id' in query_string:
        query += ' eid = %s'
        filter.append(query_string['scopus_id'])
        cur.execute(query, filter)
    elif len(query_string) == 0:
        query = query[:-4]
        cur.execute(query)
    else:
        return page_not_found(404)

    columns = list(map(lambda x: x[0], cur.description))
    results = [dict(zip(columns, x)) for x in cur.fetchall()][0]
    cur.close()
    return jsonify(results)


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


if __name__ == '__main__':
    app.run()
