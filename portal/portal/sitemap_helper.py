import json
from django.conf import settings


# Merge all site.json files
def load_all_sections(lang=None):
    # Load from the external_drive
    lang_file_modifier = ""
    if lang == "zh":
        lang_file_modifier = "_cn"
    file_dir_list = ["book", "blog", "documentation"]

    all_sections = {}
    for dir_path in file_dir_list:
        file_path = "%s/%s/site%s.json" % (settings.EXTERNAL_TEMPLATE_DIR, dir_path, lang_file_modifier)
        try:
            json_data = open(file_path).read()
            data = json.loads(json_data)
            all_sections.update(data)
        except:
            print "Missing site.json from %s" % file_path
            pass

    return all_sections


# From all the sections, out a json file with all the tutorial related sections
def load_tutorial_book(lang=None):
    if lang == "zh":
        sitemap_file_path = "tutorial_cn.json"
    else:
        sitemap_file_path = "tutorial.json"

    try:
        # Check if there is an existing tutorial.json file already
        # Reuse if possible
        with open(sitemap_file_path) as json_data:
            data = json.load(json_data)
            return data
    except IOError:
        # tutorial.json is missing. Create a new one
        chapters = ["getting_started", "tutorial", "advanced"]
        tutorial_dict = {
            "id": "tutorial",
            "title": "Tutorial",
        }

        all_sections = load_all_sections(lang)
        sections = []
        for chapter_id in chapters:
            if chapter_id in all_sections:
                sections.append(all_sections[chapter_id])

        tutorial_dict["chapters"] = sections

        # NOTE! Only output the json file when we have elements in sections.
        if sections:
            with open(sitemap_file_path, 'w') as fp:
                json.dump(tutorial_dict, fp)


        return tutorial_dict
