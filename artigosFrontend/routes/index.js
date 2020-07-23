var express = require('express');
var router = express.Router();
var axios = require('axios');

router.get('/', function (req, res, next) {
  res.redirect('/autores')
})
/* GET home page. */
router.get('/autores', function (req, res, next) {
  axios.get('http://localhost:5000/api/authors')
    .then(dados => res.render('index', { lista: dados.data }))
    .catch(erro => res.render('error', { error: erro }))
});

router.get('/autores/:orcid/artigos', function (req, res, next) {
  axios.get('http://localhost:5000/api/works?from=' + req.params.orcid)
    .then(dados => res.render('artigos_table', { data: { artigos: dados.data, orcid: req.params.orcid } }))
    .catch(erro => res.render('error', { error: erro }))
});

router.get('/autores/:orcid/scopus/:scopus_id', function (req, res, next) {
  axios.get('http://localhost:5000/api/scopus?scopus_id=' + req.params.scopus_id)
    .then(dados => res.render('more', { scopus: dados.data }))
    .catch(erro => res.render('error', { error: erro }))
})

router.get('/autores/')

module.exports = router;
