import credentials
import json
import logging
import mwclient
import os
import re
import requests
import sys
import time

logger = logging.getLogger("MediaWiki Logger")
logger.setLevel(logging.DEBUG)
if (logger.hasHandlers()):
    logger.handlers.clear()
consoleHandler = logging.StreamHandler(sys.stdout)
logger.addHandler(consoleHandler)

class WikiBot:

    def __init__(self, hostname, path, https=False):
        self.hostname = hostname
        self.site = mwclient.Site(hostname, path)
        self.url = ("https" if https else "http") + "://" + hostname
        self.path = path
        self._namespaces = None
        logger.info("Connected to site '" + self.url + "'.")

    def login(self, username, password):
        success = None
        try:
            self.site.login(username, password)
            success = True
            logger.info("User '" + username + "' has successfully logged in.")
        except:
            success = False
            logger.error("User '" + username + "' has failed to logged in.")
        return success
    
    def _get_namespaces(self, key="name"):
        if self._namespaces:
            return self._namespaces
        url = self.url + self.path + "api.php"
        query = {
            "action": "query",
            "meta": "siteinfo",
            "siprop": "namespaces",
            "formatversion": "2",
            "format": "json"
        }
        response = requests.get(url, params=query)
        namespaces = json.loads(response.text)["query"]["namespaces"]
        results = dict()
        for index in namespaces:
            namespace = namespaces[index][key]
            if namespace: # non-main namespaces
                results[namespace] = index
        self._namespaces = results
        return self._namespaces

    def get_namespaces(self):
        return self._get_namespaces(key='name')

    def download_pages(self, savepath=".", category=None, prefix=None, namespace=None, limit=None, redirects=False):
        """(self[, [str, str, str, str, int, bool]) -> int

        Downloads the wikitext of the pages queried.
        Returns the number of pages downloaded.
        """
        count = 0
        logger.info("Downloading pages...")
        namespaces = self.get_namespaces()
        # if there is a namespace specified, get the index
        namespace_index = '0'
        if namespace:
            namespace_index = namespaces[namespace]
        # go through all pages queried
        allpages = self.site.allpages(prefix=prefix, namespace=namespace_index, limit=limit)
        for page in allpages:
            # if no redirects, skip redirect
            if not redirects:
                beginning = page.text()[:10].upper()
                if beginning.startswith("#REDIRECT"):
                    continue
            # if there is a category argument, check if page is in category
            if category:
                category = "Category:" + category
                valid = True
                for catpage in page.categories():
                    valid = catpage.name == category
                if not valid:
                    continue
            # get namespace to create folder structure
            namespace = "Main"
            pagename = page.name
            if pagename.startswith(tuple(namespaces.keys())):
                namespace, pagename = pagename.split(":", 1)
            # save to folderpath
            folderpath = savepath + "/" + self.hostname + "/" + namespace
            filepath = folderpath + "/" + pagename + ".wiki"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as file_handle:
                try:
                    file_handle.write(page.text())
                except UnicodeEncodeError:
                    logger.warning("Text for '" + pagename + "' contains non-utf-8 characters.")
                    text = page.text().encode("utf-8", errors="backslashreplace")
                    text = text.decode("utf-8", errors="backslashreplace")
                    file_handle.write(text)
                count += 1
        # logger result message
        if count > 0:
            msg = str(count) + " page" + ("s have" if count > 1 else " has")
            msg += " been downloaded."
        else:
            msg = "No pages have been downloaded."
        logger.info(msg)
        return count
    
    def move_category_pages(self, old_category, new_category, delay=1):
        """(WikiBot, str, str) -> int

        Moves all pages from the specified old category to the new category.
        Returns the number of pages moved.

        Note: pages in which the category has been transcluded will not be moved.
        """
        count = 0
        for page in self.site.Categories[old_category]:
            # Check for category wikitext if there was transclusion
            replace = None
            search = None
            search0 = "[[Category:" + old_category + "]]"
            search1 = "[[Category:" + old_category + "|"
            if search0 in page.text():
                search = search0
                replace = "[[Category:" + new_category + "]]"
            elif search1 in page.text():
                search = search1
                replace = "[[Category:" + new_category + "|"
            # if there is replaceable text, commit edit
            if replace:
                newtext = page.text().replace(search, replace)
                summary = "Moved to category '" + new_category + "'"
                summary += " (automated edit)"
                page.edit(newtext, summary)
        # logger result message
        if count > 0:
            msg = str(count) + " page" + ("s have" if count > 1 else " has")
            msg += " been downloaded."
        else:
            msg = "No pages have been downloaded."
        logger.info(msg)
        return count

    def fix_spacings(self, *pages):
        section_regex = r"^(=+)\s*(.+?)\s*(=+)$"
        list_regex = r"^(\*+|#+)\s*(.*)"
        dict_regex = r"^;\s*(.*)"
        for pagename in pages:
            page = self.site.Pages[pagename]
            pagelines = page.text().split("\n")
            for i, line in enumerate(pagelines):
                # section regex
                match = re.match(section_regex, line)
                if match:
                    pagelines[i] = match.group(1) + " " + match.group(2) + " " + match.group(3)
                    continue
                # list item regex
                match = re.match(list_regex, line)
                if match:
                    pagelines[i] = match.group(1) + " " + match.group(2)
                    continue
                # dictionary regex
                match = re.match(dict_regex, line)
                if match:
                    pagelines[i] = "; " + match.group(1)
                    continue
            # commit edit
            text = "\n".join(pagelines)
            summary = "Fixed spacings (automated edit)"
            page.edit(text, summary)

    def get_wikifarm(self):
        return None


class WikiaBot(WikiBot):

    def __init__(self, sitename):
        hostname = sitename + ".fandom.com"
        WikiBot.__init__(self, hostname, "/", https=True)
        self.sitename = sitename

    def get_namespaces(self):
        return super()._get_namespaces(key="*")

    def get_wikifarm(self):
        return "Fandom"


class GamepediaBot(WikiBot):
    
    def __init__(self, sitename):
        hostname = sitename + ".gamepedia.com"
        WikiBot.__init__(self, hostname, "/", https=True)
        self.sitename = sitename

    def get_wikifarm(self):
        return "Gamepedia"


if __name__ == "__main__":
    bot = WikiaBot("youtube")
    login_success = bot.login(credentials.USERNAME, credentials.PASSWORD)    
    if login_success:
        print(bot.get_namespaces())
