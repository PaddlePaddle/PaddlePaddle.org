def download_latest_doc_workspace(request):
    portal_helper.download_and_extract_workspace()
    return redirect('/')


def blog_root(request):
    path = menu_helper.get_external_file_path('blog/index.html')

    return render(request, 'content.html', {
        'static_content': _get_static_content_from_template(path),
        'content_id': Content.BLOG
    })


def blog_sub_path(request, path):
    static_content_path = menu_helper.get_external_file_path(request.path)

    return render(request, 'content.html', {
        'static_content': _get_static_content_from_template(static_content_path),
        'content_id': Content.BLOG
    })


def other_path(request, version, path=None):
    """
    Try to find the template associated with this path.
    """
    try:
        # If the template is found, render it.
        static_content_template = get_template(
            menu_helper.get_external_file_path(request.path))

    except TemplateDoesNotExist:
        # Else, fetch the page, and run through a generic stripper.
        fetch_and_transform(url_helper.GITHUB_ROOT + '/' + os.path.splitext(path)[0] + '.md', version)

    return _render_static_content(request, path, version, Content.OTHER)


def flush_other_page(request, version):
    """
    To clear the contents of any "cached" arbitrary markdown page, one can call
    *.paddlepaddle.org/docs/{version}/flush?link={...example.com/page.md}&key=123456
    """
    secret_subkey = request.GET.get('key', None)
    link = request.GET.get('link', None)

    if secret_subkey and secret_subkey == settings.SECRET_KEY[:6]:
        page_path = settings.OTHER_PAGE_PATH % (
            settings.EXTERNAL_TEMPLATE_DIR, version, os.path.splitext(
            urlparse(link).path)[0] + '.html')
        try:
            os.remove(page_path)
            return HttpResponse('Page successfully flushed.')

        except:
            return HttpResponse('Page to flush not found.')
