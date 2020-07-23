import sys
import getopt
import requests
import json
import tqdm as tqdm
import numpy as np
import mysql.connector as MySQL

client_id = 'APP-S1SLC8UQKLIKHNEC'
scopus_key = '795cf63e84e057cde662b915f5f86c80'
api_key = '7777cd59-8ae0-4685-a58a-e72ab66ef7d3'
orcid_id = '0000-0003-4121-6169'
headers_dict = {'Content-Type': 'application/json'}
# 0000-0003-3957-2121 | 35 - Works
# 0000-0001-9710-847X | 11 - Works
# 0000-0003-4121-6169 | 280 - works


def parse_args(argv):
    arguments_list = argv[1:]
    short_options = "a:"
    long_options = ["author="]

    try:
        opts, args = getopt.getopt(
            arguments_list, short_options, long_options)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    for opt, arg in opts:
        if opt in ['-a', '--author']:
            if len(arg) != 19:
                print('Orcid ID com tamanho incorreto. Formato -> "nnnn-nnnn-nnnn-nnnn"')
                sys.exit(2)
            else:
                orcid_id = arg.strip()
                return orcid_id


def get_author_info(orcid_id):
    route = 'https://pub.orcid.org/v3.0/' + orcid_id + '/person'
    print(route, '\n')
    try:
        resp = requests.get(route, headers=headers_dict)
        if resp:
            resp_json = resp.json()
            print(resp_json)

            names_dict = resp_json['name']
            bio_dict = resp_json['biography']

            name = names_dict['given-names']['value'] + \
                '  ' + names_dict['family-name']['value']
            bio = (bio_dict['content']).split('.')[0]

            return (orcid_id, name, bio)
        else:
            print(
                f"https://pub.orcid.org/v3.0/{orcid_id}/person | Status Code: {resp.status_code}")
            sys.exit(2)

    except requests.exceptions.RequestException as e:
        print(e)


def get_article_ids(orcid_id):
    resp = requests.get("https://pub.orcid.org/v3.0/" + orcid_id + "/works",
                        headers=headers_dict)
    if resp:
        resp_json = resp.json()
        articles = resp_json['group']

        articles_eids = []
        articles_putCodes = []
        articles_wosids = []

        for idx, article in enumerate(articles):
            for ext_id_dict in article['external-ids']['external-id']:
                if ext_id_dict['external-id-type'] == 'eid':
                    articles_eids.append(ext_id_dict['external-id-value'])
                if ext_id_dict['external-id-type'] == 'wosuid':
                    articles_wosids.append(ext_id_dict['external-id-value'])
            if len(articles_eids)-1 < idx:
                articles_eids.append('None')
            if len(articles_wosids)-1 < idx:
                articles_wosids.append('None')

            articles_putCodes.append(article['work-summary'][0]['put-code'])

        if len(articles_eids) == len(articles_putCodes):
            articles_ids = dict(zip(np.arange(len(articles_eids)),
                                    zip(articles_putCodes, articles_eids, articles_wosids)))
            return articles_ids
        else:
            print('Listas com tamanhos diferentes')
            return
    else:
        print(
            f"https://pub.orcid.org/v3.0/{orcid_id}/works | Status Code: {resp.status_code}")
        sys.exit(2)


def get_articles_info(articles_ids, orcid_id):
    artigos = []
    scopus_info = []
    orcid_route = 'https://pub.orcid.org/v3.0/'
    # scopus_route

    for key, values in articles_ids.items():
        print(f'Artigos: {len(artigos)}\nScopus: {len(scopus_info)}\n')
        putCode = values[0]
        eid = values[1]
        wosid = values[2]

        if eid == 'None':
            resp = requests.get(
                f'{orcid_route}{orcid_id}/works/{putCode}', headers=headers_dict)
            resp_json = resp.json()
            work = resp_json['bulk'][0]['work']

            try:
                title = work['title']['title']['value']
            except KeyError:
                title = 'None'

            try:
                publication_date = work['publication-date']['year']['value']
            except:
                publication_date = 'None'

            try:
                typea = work['type']
            except:
                typea = 'None'

            try:
                n_contributors = len(work['contributors']['contributor'])
            except KeyError:
                n_contributors = 'None'

            try:
                journal_title = work['journal-title']['value']
            except:
                journal_title = 'None'

            try:
                url = work['url']['value']
            except:
                url = 'None'

            # print(title, publication_date, typea,
            #      n_contributors, journal_title, url)
            artigos.append((putCode, eid, wosid, title,
                            publication_date, typea, n_contributors, journal_title, url))
        else:
            scopus_id = eid.split('-')[-1]
            url = ("https://api.elsevier.com/content/abstract/scopus_id/")
            resp = requests.get(
                url+scopus_id, headers={'Accept': 'application/json', 'X-ELS-APIKey': scopus_key})
            print(url+scopus_id)
            resp_json = json.loads(resp.text.encode('utf-8'))
            try:
                work = resp_json["abstracts-retrieval-response"]
            except KeyError:
                continue

            # work
            title = work['coredata']['dc:title']
            publication_date = work['coredata']['prism:coverDate']
            typea = work['coredata']['subtypeDescription']
            n_contributors = len(work['authors']['author'])

            try:
                keywords_list = work['authkeywords']['author-keyword']
                if isinstance(keywords_list, list):
                    keywords = [x['$'] for x in keywords_list]
                else:
                    keywords = 'None'

                if isinstance(keywords, list):
                    keywords = ', '.join(keywords)
            except (KeyError, TypeError):
                keywords = 'None'

            try:
                journal_title = work['coredata']['dc:publisher']
            except KeyError:
                journal_title = 'None'

            url = work['coredata']['prism:url']

            # scopus data
            try:
                isbn = work['coredata']['prism:isbn']
                if isinstance(isbn, str):
                    pass
                else:
                    isbn = isbn[0]['$']
            except:
                isbn = 'None'

            try:
                issn = work['coredata']['prism:issn']
                issn = issn.split()[0]
            except:
                issn = 'None'

            try:
                srcid = work['coredata']['source-id']
            except:
                srcid = 'None'
            try:
                citations = work['coredata']['citedby-count']
            except KeyError:
                citations = 'None'
            try:
                contributors = [x['preferred-name']['ce:indexed-name']
                                for x in work['authors']['author']]
            except KeyError:
                contributors = 'None'
            artigos.append((putCode, eid, wosid, title,
                            publication_date, typea, n_contributors, journal_title, url))

            # print('Work\n')
            # print(title, publication_date, typea,
            #       n_contributors, journal_title, url)
            # print('scopus data\n')
            # print(isbn, citations, contributors)
            # print(type(isbn))
            # print(isbn)
            if isbn == 'None':
                ano = 'None'
                sjr = 'None'
            else:
                url_t = 'https://api.elsevier.com/content/serial/title/isbn/' + \
                    isbn + ' ?apiKey=' + scopus_key
                isbn_res = requests.get(
                    url_t, headers={'Accept': 'application/json'})
                isbn_res_json = isbn_res.json()
                # print(type(isbn))
                # print(isbn_res_json.keys())
                try:
                    years_list = isbn_res_json['serial-metadata-response']['entry']
                except KeyError:
                    years_list = 'None'
                try:
                    ano = years_list[-1]['SJRList']['SJR'][0]['@year']
                except KeyError:
                    ano = 'None'
                try:
                    sjr = years_list[-1]['SJRList']['SJR'][0]['$']
                except KeyError:
                    sjr = 'None'

            if isinstance(contributors, list):
                contributors = ', '.join(contributors)

            scopus_info.append(
                (eid, citations, isbn, issn, srcid, keywords, contributors, ano, sjr))

    return artigos, scopus_info


def insert_into_bd(autor, works, scopus_info):
    # Statements de inserção
    author_query = 'INSERT INTO AUTHOR(orcid_id, name, biography) values (%s,%s,%s)'
    works_query = 'INSERT INTO WORK(putcode, eid, wosid, title, publication_date, type, n_contributors, journal_title, url) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    author_works_query = 'INSERT INTO AUTHOR_WORK(author_id, work_id) values (%s, %s)'
    scopus_query = 'INSERT INTO SCOPUS_INFO(eid, citations, isbn, issn, srcid, keywords, authors, ano, sjr) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
    check_works_query = 'SELECT work_id, putcode, eid, title FROM work'
    check_scopus_query = 'SELECT eid from scopus_info'

    # Conexão à bd
    db_con = MySQL.connect(host="localhost", user="root",
                           passwd="root", db="articlesdb")

    # Verifica que works e scopus_info já existem;
    check_works_cur = db_con.cursor()
    check_works_cur.execute(check_works_query)
    bd_works = check_works_cur.fetchall()
    check_works_cur.close()

    inserted_works_ids = [work[0]
                          for work in bd_works if work[3].lower() in [y[3].lower() for y in works]]

    works = [work for work in works if work[3].lower() not in [y[3].lower()
                                                               for y in bd_works]]

    scopus_info = [info for info in scopus_info if info[0]
                   not in [y[2] for y in bd_works]]

    # Verifica que scopus_info e scopus_info já existem;
    check_scopus_cur = db_con.cursor()
    check_scopus_cur.execute(check_scopus_query)
    bd_scopus = check_scopus_cur.fetchall()
    check_scopus_cur.close()

    scopus_info = [info for info in scopus_info if info[0]
                   not in [y[0] for y in bd_scopus]]

    print(works, '\n')
    print(scopus_info, '\n')
    print(inserted_works_ids, '\n')
    # Cursor inserção Autor
    author_cur = db_con.cursor()
    try:
        author_cur.execute(author_query, (autor))
    except(MySQL.Error, MySQL.Warning) as e:
        print(e)
        author_cur.close()
        db_con.close()
        return
    author_id = author_cur._last_insert_id
    author_cur.close()

    # INSERTED AUTHOR_WORKS
    inserted_author_works = [(author_id, x) for x in inserted_works_ids]
    print(inserted_author_works)

    if len(scopus_info) > 0:
        # Scopus_info
        scopus_info_cur = db_con.cursor()
        try:
            scopus_info_cur.executemany(scopus_query, tuple(scopus_info))
        except(MySQL.Error, MySQL.Warning) as e:
            print(e)
            scopus_info_cur.close()
            db_con.close()
            return
        scopus_info_cur.close()

    # Works cursor
    if len(works) > 0:
        works_cur = db_con.cursor()
        try:
            works_cur.executemany(works_query, tuple(works))
            id_fw_inserted = works_cur._last_insert_id
            print(id_fw_inserted)
            works_cur.close()
        except(MySQL.Error, MySQL.Warning) as e:
            print(e)
            works_cur.close()
            db_con.close()
            return

    print('Works inseridos')

    # Author_work
    if len(works) > 0:
        author_works = [(author_id, x)
                        for x in range(id_fw_inserted, (id_fw_inserted + len(works)))]

        if len(inserted_author_works) > 0:
            author_works += inserted_author_works
    else:
        author_works = inserted_author_works

    print(author_works)
    author_work_cur = db_con.cursor()
    try:
        author_work_cur.executemany(author_works_query, tuple(author_works))
    except(MySQL.Error, MySQL.Warning) as e:
        print(e)
        author_work_cur.close()
        db_con.close()
        return
    author_work_cur.close()

    # Commit final e fecho da conexão à bd
    db_con.commit()
    db_con.close()


def main(args):
    orcid_id = parse_args(args)

    # autor = tuple(orcid_id, name, bio)
    author = get_author_info(orcid_id)

    # dict of articles id's | key (article_index), values [article_putCode, article_eid]
    articles_ids = get_article_ids(orcid_id)

    # # list of articles | list of scopus information about articles with eid
    articles, scopus_info = get_articles_info(articles_ids, orcid_id)

    # # Insert into bd
    insert_into_bd(author, articles, scopus_info)

    # # {key: articles_ids[key] for key in np.arange(80)}


if __name__ == "__main__":
    main(sys.argv)
