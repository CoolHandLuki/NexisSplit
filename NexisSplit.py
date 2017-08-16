import sys, codecs, os, re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

months = ["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
corpus = "Korpus.TXT"
regex = "Dokument\ [0-9]{1,3}\ von\ [\0-9]{1,3}"

class LexisNexisSplitter():
    def __init__(self, regex, corpus, months):
        super(LexisNexisSplitter, self).__init__()
        self.regex = regex
        if type(corpus) == str:
            with codecs.open(corpus, "r") as f:
                self.corpus = f.readlines()
        elif type(corpus) == list:
            self.corpus = corpus
        else:
            raise ValueError("Call LexisNexisSplitter like this:\nLexisNexisSplitter('regular expression', 'corpus' (either as path to file or already loaded into a list), 'months' (as a list of strings)")
        # Expect either an already loaded corpus (list) or a (str) as path
        # in case the splitter is invoked from the GUI or from command line.
        # If corpus references to neither a string nor a list, raise an error.

        self.BOM = self.corpus[0].rstrip()
        # Save the byte order mark because we'll be splitting the corpus into
        # smaller portions and every one of those needs to have the BOM in the
        # start of its byte stream or other applications might have to guess
        # the encoding and will probably be wrong.

        self.regex = re.compile(regex)
        self.monthsConversionTable = {str(months[i]).zfill(2): i+1 \
                                      for i in range(len(months))}

    def _split_corpus(self):
        splitCorpus = re.split(self.regex, "".join(self.corpus))[1:]
        # Don't save the first element because it's BEFORE the first
        # article (meaning only the BOM and some empty lines)

        self.articles = []
        for article in splitCorpus:
            text = []
            for line in article.split("\n"):
                if self.BOM in line:
                    pass
                elif line.isspace():
                    pass
                elif line == "":
                    pass
                # Don't append the BOM so in case we process the same
                # article multiple times the BOMs don't multiply (it is
                # added later at each file save). Also don't append empty
                # lines.
                    
                else:
                    text.append(line.rstrip())
            self.articles.append(LexisNexisArticle(text, \
                                                   self.monthsConversionTable))

    def _group_articles_by_date(self):
        self.articlesByDate = {}
        self.earliestDate = "99999999"
        self.latestDate = "00000000"
        # Create two lists to store the date of our first and last article,
        # which we might need if our corpus doesn't contain an article on each
        # date and we don't want gaps in our graphs later (e.g.: we will
        # generate a range of dates ourselves).
        
        for article in self.articles:
            if article.date in self.articlesByDate.keys():
                self.articlesByDate[article.date].append(article)
            else:
                self.articlesByDate[article.date] = [article]
            # If a key sure already exists, add our article to that key, if
            # not, add the key and then the article.
            
            if article.date < self.earliestDate:
                self.earliestDate = article.date
            elif article.date > self.latestDate:
                self.latestDate = article.date
            # Update earliestDate and latestDate if we find an earlier or later
            # date.
        
    def _group_articles_by_medium(self):
        self.articlesByMedium = {}
        for article in self.articles:
            if article.medium in self.articlesByMedium.keys():
                self.articlesByMedium[article.medium].append(article)
            else:
                self.articlesByMedium[article.medium] = [article]

    def _prepare_frequency_plotting(self):
        dateRange = pd.date_range(start=self.earliestDate, \
                                  end=self.latestDate, freq="D")
        # Build a dateRange over entire duration of our corpus as our index
        # for the x-axis and to catch dates on which zero articles were
        # published.
        
        articlesPerDay = []
        for date in dateRange:
            dateKey = "".join([str(date.year), str(date.month).zfill(2), \
                               str(date.day).zfill(2)])
            if dateKey in self.articlesByDate.keys():
                articlesPerDay.append(len(self.articlesByDate[dateKey]))
            else:
                articlesPerDay.append(0)
        self.df = pd.DataFrame(articlesPerDay, \
                    index=dateRange, columns=["articles"])
        # Create a DataFrame object from our articles per day, using the date
        # time indexes as an index.

    def _save_articles(self, mode="byNumber", path=None, docSeparator=None):
        if path == None:
            raise ValueError("Path is not set!")
        else:
            self.docSeparator = docSeparator + "\n"
            currentDir = os.getcwd()
            os.chdir(path)
            newDir = str(mode) + "_" + datetime.now().strftime("%Y%m%d%H%M%S")
            os.mkdir(newDir)
            os.chdir(newDir)
            if mode == "byNumber":
                length = len(self.articles)
                for i in range(0, length):
                    fileName = str(i).zfill(len(str(length))) + ".txt"
                    with open(fileName, "w") as f:
                        f.write(self.BOM + "\n")
                        f.write(self.docSeparator)
                        f.write("\n".join(self.articles[i].text))
                        
            elif mode == "byDate":
                for date in self.articlesByDate.keys():
                    length = len(self.articlesByDate[date])
                    os.mkdir(date)
                    os.chdir(date)
                    for i in range(0, length):
                        fileName = str(i).zfill(len(str(length))) + ".txt"
                        with open(fileName, "w") as f:
#                            f.write(self.BOM + "\n")
#                            f.write(self.docSeparator)
                            f.write("\n".join \
                                    (self.articlesByDate[date][i].text))
                    os.chdir("..")
                    
            elif mode == "byMedium":
                for medium in self.articlesByMedium.keys():
                    saneName = ""
                    for s in str(medium):
                        if s.isalpha():
                            saneName += s
                    if len(saneName) == 0:
                        raise ValueError(str(medium) + "does not contain any alphabetic letters?")
                    # Sanitize the name of our medium by just allowing letters
                    # from the alphabet.
                    
                    length = len(self.articlesByMedium[medium])
                    os.mkdir(saneName)
                    os.chdir(saneName)
                    for i in range(0, length):
                        fileName = str(i).zfill(len(str(length))) + ".txt"
                        with open(fileName, "w") as f:
                            f.write(self.BOM + "\n")
                            f.write(self.docSeparator)
                            f.write("\n".join(self.articlesByMedium[medium][i]\
                                              .text))
                    os.chdir("..")                    
            os.chdir(currentDir)
            
class LexisNexisArticle():
    def __init__(self, text, monthsConversionTable):
        super(LexisNexisArticle, self).__init__()
        keepMetaData = False # Placeholder, make this an option in the GUI!
        if keepMetaData is True:
            self.text = text
        else:
            self.text = text[2:]
        # Keep or discard metadata (date & medium string) depending on wether
        # the generated files will be processed again.

        self.medium = None
        self.date = None
        while self.date == None:
            for line in text:
                if self.medium == None:
                    self.medium = line.strip()
                elif self.date == None:
                    #try:
                    self.date = self._format_date(line.strip(),\
                                                      monthsConversionTable)
                    #except Exception as e:
                    #    print("\n\n\n" + str(self.text) + "\n" + \
                    #    self.medium +"Exception" + str(e) + "encountered")
                else:
                    break
                # Once we've set medium & date, exit.

    def _format_date(self, date, monthsConversionTable):
        dateList = date.split()
        if dateList[0][0].isalpha() is True:
            # If dateList starts with the day of the week the date sits in:
            # [1:3].
            day, month, year = dateList[1], dateList[2], dateList[3]
        else:
            # If dateList starts with a number the date sits in: [0:2].
            day, month, year = dateList[0], dateList[1], dateList[2]
        try:
            month = str(monthsConversionTable[month]).zfill(2)
        except KeyError as e:
            print("Encountered ", e, "while processing: ", date)
        # Use the conversion table to get the right numeric representation of
        # each month and .zfill to format all days to two digits.

        day = re.search(re.compile("[0-9]{1,2}"), day).group().zfill(2)
        year = re.search(re.compile("[0-9]{4}"), year).group()
        # Sanitize day and year and ensure that days 1-9 have a leading zero.
                            
        date = "".join([year, month, day])
        return date
    
def main():
    splitter = LexisNexisSplitter(regex, corpus, months)
    splitter._split_corpus()
#    splitter._group_articles_by_date()
#    splitter._group_articles_by_medium()
#    splitter._prepare_frequency_plotting()
    return splitter
    
if __name__ == "__main__":
    splitter = main()
