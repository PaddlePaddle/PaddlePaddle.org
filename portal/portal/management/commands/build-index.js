// Inspired from https://lunrjs.com/guides/index_prebuilding.html.

var lunr = require('../../static/js/lunr'),
    fs = require('fs'),
    stdout = process.stdout;

var filename = process.argv[2],
    contents = fs.readFileSync(filename, 'utf8');

var documents = JSON.parse(contents);

var idx = lunr(function () {
    this.ref('id');
    this.field('title', { boost: 20 });
    this.field('content');

    documents.forEach(function (doc) {
        this.add(doc);
    }, this);
});

stdout.write(JSON.stringify(idx))
