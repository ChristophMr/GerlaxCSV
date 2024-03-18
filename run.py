import xml.etree.ElementTree as ET
import csv
import re
import sys

class Paragraph: 
    def __init__(self) -> None:
        self.paragraphNumber = ""
        self.sectionNumber = "" #Absnummer
        self.number = ""
        self.literal = ""
        self.subLiteral = ""
        self.content = ""
        pass

    def sanitizeCsvStringValue(contentValue):
        return contentValue
    
    def toString(self):
        content = ""
        return self.paragraphNumber + ";" + self.sectionNumber + ";" + self.number + ";" + self.literal + ";" + self.subLiteral + ";" + content
    
    def toArray(self): 
        return [self.paragraphNumber, self.sectionNumber, self.number, self.literal, self.subLiteral, self.content]

    def clone(self): 
        paragraph = Paragraph()
        paragraph.paragraphNumber = self.paragraphNumber
        paragraph.sectionNumber = self.sectionNumber
        paragraph.number = self.number
        paragraph.literal = self.literal
        paragraph.subLiteral = self.subLiteral
        paragraph.content = self.content

        return paragraph

def write_to_csv(file_path, data):
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Paragraph (“§”)', 'Absatz “(1)”', 'Nummer “1.”', 'Buchstabe “a)”', 'Buchstabe 2 “aa)”', 'Inhalt'])
        for norm in data:
            writer.writerow(norm.toArray())

def parseNormNode(norm_node): 
    metadataNode = norm_node.find('.//metadaten')
    paragraphs = []

    paragraphObj = Paragraph()

    if (isValidNormNode(metadataNode) == False):
        return None
    
    enbezNode = metadataNode.find('.//enbez')
    titelNode = metadataNode.find('.//titel')
    paragraphObj.paragraphNumber = enbezNode.text
    paragraphObj.content = titelNode.text

    paragraphs.append(paragraphObj)
    contentNode = getContentNode(norm_node)

    if (contentNode is None):
        return None

    for paragraph in evaluateSections(paragraphObj, contentNode):
        paragraphs.append(paragraph)

    return paragraphs

def evaluateSections(paragraphObj, contentNode):
    pNodes = contentNode.findall('.//P')
    paragraphResults = []

    for pNode in pNodes:
        paragraphClone = paragraphObj.clone()

        #for cases where law paragraph is no longer in force (Weggefallen)
        if (pNode.text == None):
            continue

        paragraphClone = setSectionInfo(paragraphClone, pNode)
        paragraphResults.append(paragraphClone)

        pEvalNodeClone = paragraphClone.clone()

        for paragraph in evaluateDtArea(pEvalNodeClone, pNode):
            paragraphResults.append(paragraph)
        

    return paragraphResults

def setSectionInfo(paragraphClone, pNode):
    pText = pNode.text

    sectionNumber = str(get_first_number_in_parentheses(pText))
    pText = remove_first_number_in_parentheses(pText)

    paragraphClone.sectionNumber = sectionNumber
    paragraphClone.content = pText

    return paragraphClone

def evaluateLaNode(nodes):
    laNodes = []

    for node in nodes: 
        if node.tag == "LA": 
                    laNodes.append(node)

        headerLaNode = None
        contentLaNode = None
        laContent = None

        if (len(laNodes) > 1):
            headerLaNode = laNodes[0]
            contentLaNode = laNodes[1]

            laContent = headerLaNode.text + ' ' + contentLaNode.text
        else: 
            contentLaNode = laNodes[0]
            laContent = contentLaNode.text

    return laContent, contentLaNode

def evaluateDtArea(paragraphClone, pNode): 
    dlNode = pNode.find('.//DL')
    dtNode = None
    ddNode = None

    paragraphResults = []

    if (dlNode is None):
        return paragraphResults

    for subNode in dlNode: 
        if (subNode.tag == "DT"):
            dtNode = subNode

        if (subNode.tag == "DD"):
            ddNode = subNode

        if (dtNode != None and ddNode != None):
            laContent, contentLaNode = evaluateLaNode(ddNode)

            paragraphClone.number = dtNode.text
            paragraphClone.content = laContent

            cloneRes = paragraphClone.clone()

            paragraphResults.append(cloneRes)

            for res in evaluateLANode(cloneRes, contentLaNode):
                paragraphResults.append(res)

            dtNode = None
            ddNode = None

    return paragraphResults

def evaluateLANode(paragraphClone, laNode):
    dlNode = laNode.find('.//DL')
    dtNode = None
    ddNode = None

    paragraphResults = []

    if (dlNode is None):
        return paragraphResults

    for subNode in dlNode: 
        if (subNode.tag == "DT"):
            dtNode = subNode

        if (subNode.tag == "DD"):
            ddNode = subNode

        if (dtNode != None and ddNode != None):
            laContent, contentLaNode = evaluateLaNode(ddNode)

            cloneRes = paragraphClone.clone()
            cloneRes.literal = dtNode.text
            cloneRes.content = laContent
            
            paragraphResults.append(cloneRes)

            for subLiteralParagraph in evaluateSubliteralNode(cloneRes, contentLaNode):
                paragraphResults.append(subLiteralParagraph)

            dtNode = None
            ddNode = None

    return paragraphResults

def evaluateSubliteralNode(paragraphClone, laNode):
    dlNode = laNode.find('.//DL')
    dtNode = None
    ddNode = None

    paragraphResults = []

    if (dlNode is None):
        return paragraphResults

    for subNode in dlNode: 
        if (subNode.tag == "DT"):
            dtNode = subNode

        if (subNode.tag == "DD"):
            ddNode = subNode

        if (dtNode != None and ddNode != None):
            laContent, contentLaNode = evaluateLaNode(ddNode)

            cloneRes = paragraphClone.clone()
            cloneRes.subLiteral = dtNode.text
            cloneRes.content = laContent
            
            paragraphResults.append(cloneRes)

            dtNode = None
            ddNode = None

    return paragraphResults

def remove_first_number_in_parentheses(text):
    pattern_number = r'\(\d+[a-zA-Z]*\)'
    result = re.sub(pattern_number, '', text, count=1)
    result = re.sub(r'^\s+', '', result)
    return result

def get_first_number_in_parentheses(input_string):
    pattern = r'\((\d+[a-zA-Z]*)\)'
    matches = re.findall(pattern, input_string)

    if len(matches) > 0:
        return matches[0]
    
    return ""

def getContentNode(norm_node):
    textdataNode = norm_node.find('.//textdaten')

    if textdataNode is None:
        return None 

    textdataSubNode = textdataNode.find('.//text')

    if (textdataNode is None):
        return None
    
    textdataContentNode = textdataSubNode.find('.//Content')

    return textdataContentNode

def isValidNormNode(metadataNode):
    enbezNode = metadataNode.find('.//enbez')
    titleNode = metadataNode.find('.//titel')

    return enbezNode != None and titleNode != None

def main(xml_file_path, csv_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    norm_nodes = root.findall('.//norm')
    data = []
    for norm_node in norm_nodes:
        paragraph = parseNormNode(norm_node)

        if (paragraph != None):
            for p in paragraph:
                data.append(p)
                    
    #for dataentry in data: 
        #print(dataentry.toString())

    write_to_csv(csv_file_path, data)

if __name__ == "__main__":
    
    xml_file_path = sys.argv[1]
    csv_file_path = sys.argv[2]

    #xml_file_path = "/Users/christophmaier/Documents/Projekte/law_xml/data/BJNR197010005.xml"
    #csv_file_path = "/Users/christophmaier/Documents/Projekte/law_xml/data/result.csv"
    main(xml_file_path, csv_file_path)

