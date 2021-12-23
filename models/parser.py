from vncorenlp import VnCoreNLP
import os
import re

pathToJar = "../Assignment/VnCoreNLP-1.1.1.jar"
annotator = VnCoreNLP(pathToJar, annotators="wseg", max_heap_size='-Xmx2g')


class Relation:
    # A relation arc of left -> right
    def __init__(self, left, relation_name, right):
        self.left = left
        self.right = right
        self.relation_name = relation_name

    def __str__(self):
        return self.relation_name + "(" + self.left + "->" + self.right + ")"

    def __eq__(self, other):
        return ((self.left == other.left) and (self.right == other.right))

    # def __hash__(self):
    #     return self.left + " " + self.right

class Configuration:
    def __init__(self, stack, buffer, arcs):
        self.stack = stack
        self.buffer = buffer
        self.arcs = arcs


class Token():
    def __init__(self, word, type):
        self.type = type
        self.word = word
        self.children = []

    def add(self, node_to_add):
        self.children.append(node_to_add)

    def __str__(self):
        if self.children:
            if "-from" in self.word:
                return "{} [{}]".format(self.type + " " + self.word[:-5],
                                        ", ".join(str(c) for c in self.children if str(c) != ""))
            elif "-to" in self.word:
                return "{} [{}]".format(self.type + " " + self.word[:-3],
                                        ", ".join(str(c) for c in self.children if str(c) != ""))
            else:
                return "{} [{}]".format(self.type + " " + self.word,
                                        ", ".join(str(c) for c in self.children if str(c) != ""))
        else:
            if self.type != "<none>":
                if "-from" in self.word:
                    return "{}".format(self.type + " " + self.word[:-5])
                elif "-to" in self.word:
                    return "{}".format(self.type + " " + self.word[:-3])
                else:
                    return "{}".format(self.type + " " + self.word)
            else:
                return ""


class Transition:

    @staticmethod
    def left_arc(conf, relation, file=None):
        """
        Add dependency relation (w_j, relation, w_i), pop stack
        :param conf: the current configuration, it has 3 elements: stack, buffer, arcs
        :param relation: the relation to be added
        """
        # Precondition: Neither the buffer nor the stack is empty
        if not conf.buffer or not conf.stack:
            return -1
        # Precondition: The word on top of the stack is not the root
        elif not conf.stack[-1]:
            return -1

        w_j = conf.buffer[0]
        w_i = conf.stack.pop()

        conf.arcs.append(Relation(w_j, relation, w_i))
        print(
            f"{'Left arc ' + relation:<25}  {'[' + ', '.join(item for item in conf.stack) + ']':<40} {'[' + ', '.join(item for item in conf.buffer) + ']':<100} {'[' + ', '.join(str(arc) for arc in conf.arcs) + ']'}",
            file=file)

    @staticmethod
    def right_arc_star(conf, relation, file=None):
        """
        Add dependency relation (w_i, relation, w_j), reduce buffer
        :param conf: the current configuration, it has 3 elements: stack, buffer, arcs
        :param relation: the relation to be added
        """
        w_j = conf.buffer[0]
        w_i = conf.stack[-1]

        conf.buffer = conf.buffer[1:]
        conf.arcs.append(Relation(w_i, relation, w_j))
        print(
            f"{'Right arc star ' + relation:<25}  {'[' + ', '.join(item for item in conf.stack) + ']':<40} {'[' + ', '.join(item for item in conf.buffer) + ']':<100} {'[' + ', '.join(str(arc) for arc in conf.arcs) + ']'}",
            file=file)

    @staticmethod
    def right_arc(conf, relation, file=None):
        """
        Add dependency relation (w_i, relation, w_j), append stack, reduce buffer
        :param conf: the current configuration, it has 3 elements: stack, buffer, arcs
        :param relation: the relation to be added
        """
        # Precondition: Neither the buffer nor the stack is empty
        if not conf.buffer or not conf.stack:
            return -1
        w_i = conf.stack[-1]
        w_j = conf.buffer[0]
        conf.stack.append(w_j)
        conf.buffer = conf.buffer[1:]
        conf.arcs.append(Relation(w_i, relation, w_j))
        print(
            f"{'Right arc ' + relation:<25}  {'[' + ', '.join(item for item in conf.stack) + ']':<40} {'[' + ', '.join(item for item in conf.buffer) + ']':<100} {'[' + ', '.join(str(arc) for arc in conf.arcs) + ']'}",
            file=file)

    @staticmethod
    def shift(conf, file=None):
        """
        Push first element in buffer on to the stack
         :param conf: the current configuration, it has 3 elements: stack, buffer, arcs
        """

        conf.stack.append(conf.buffer[0])
        conf.buffer = conf.buffer[1:]
        print(
            f"{'Shift ':<25}  {'[' + ', '.join(item for item in conf.stack) + ']':<40} {'[' + ', '.join(item for item in conf.buffer) + ']':<100} {'[' + ', '.join(str(arc) for arc in conf.arcs) + ']'}",
            file=file)

    @staticmethod
    def reduce(conf, file=None):
        """
        Pop last element of the stack
        :param conf: the current configuration, it has 3 elements: stack, buffer, arcs
        """

        # Precondition: The last element must be independent on other words
        if conf.stack[-1] not in [ele.right for ele in conf.arcs]:
            return -1
        conf.stack.pop()
        print(
            f"{'Reduce ':<25}  {'[' + ', '.join(item for item in conf.stack) + ']':<40} {'[' + ', '.join(item for item in conf.buffer) + ']':<100} {'[' + ', '.join(str(arc) for arc in conf.arcs) + ']'}",
            file=file)


def city_name_encode(city_name):
    if city_name == "hồ_chí_minh":
        return "HCMC"
    elif city_name == "hà_nội":
        return "HN"
    elif city_name == "đà_nẵng":
        return "DANANG"
    elif city_name == "huế":
        return "HUE"
    elif city_name == "nha_trang":
        return "NTrang"


def city_name_decode(city_code):
    if city_code == "HCMC":
        return "Hồ Chí Minh"
    elif city_code == "HN":
        return "Hà Nội"
    elif city_code == "DANANG":
        return "Đà Nẵng"
    elif city_code == "HUE":
        return "Huế"
    elif city_code == "NHATRANG":
        return "Nha Trang"


class ProcessText:
    """
    Class to process text
    """

    @staticmethod
    def preprocessing(text):
        text = text.lower()

        def isHaveVerb(text_list):
            # Only allow 1 word atm (chạy)
            for check_word in text_list:
                if check_word == "chạy":
                    return True
            return False

        def getFistPrepIdx(text_list):
            # 4 prep
            for i in range(len(text_list)):
                if text_list[i] in ["đến", "từ", "lúc", "hết"]:
                    return i
            return -1

        def addRealVerb(text_list):
            if not isHaveVerb(text_list):
                idx_to_add = getFistPrepIdx(text_list)
                text_list.insert(idx_to_add, "chạy")

        # This part is made specially for the command "Thời gian .... " -> "... hết bao lâu?"
        def changeCommandToQuestion(text):
            if text.startswith("thời gian "):
                # Erase that part and last character, then add the question suffix
                if text.find('mấy giờ') != -1:
                    text = text.replace('mấy giờ', '')

                text = text.replace("thời gian ", "")[:-1] + "hết bao lâu?"
            return text

        # Convert some word into normal form for easier to progress, the equivalent file is opened
        def textConvert(text_to_convert):
            dict_equiv = dict()
            with open('../Assignment/models/equivalent.txt', 'r') as file:
                info = file.read().splitlines()
                for line in info:
                    rough_texts, normal_text = line.split("->")
                    rough_text = rough_texts.split(',')
                    for text_part in rough_text:
                        dict_equiv.setdefault(text_part, normal_text)
            if "city" in text_to_convert:
                text_to_convert = text_to_convert.replace("city", "")
            if "là" in text_to_convert:
                text_to_convert = text_to_convert.replace("là", "")
            if "có" in text_to_convert:
                text_to_convert = text_to_convert.replace("có", "")
            if "giờ" in text_to_convert:
                if text_to_convert.find("mấy giờ") != -1:
                    text_to_convert = text_to_convert.replace("mấy giờ", "")
                text_to_convert = text_to_convert.replace("giờ", "hr")
            if "chuyến tàu hỏa" in text_to_convert:
                text_to_convert = text_to_convert.replace("chuyến tàu hỏa", "tàu hỏa")
            elif "chuyến tàu" in text_to_convert:
                text_to_convert = text_to_convert.replace("chuyến tàu", "tàu")

            for key in dict_equiv:
                if key in text_to_convert:
                    if key == "cố đô":
                        if "cố đô huế" in text_to_convert:
                            text_to_convert = text_to_convert.replace("cố đô huế", dict_equiv["cố đô huế"])
                        else:
                            text_to_convert = text_to_convert.replace(key, dict_equiv[key])
                    else:
                        text_to_convert = text_to_convert.replace(key, dict_equiv[key])
            return text_to_convert

        # Convert time in VNese to suitable form
        def timeConvert(text_to_convert):
            text_convert_split = text_to_convert.split()
            for idx in range(len(text_convert_split)):
                if text_convert_split[idx] == "hr":
                    updated_time = main_time = ""
                    if idx + 1 < len(text_convert_split):
                        if text_convert_split[idx + 1] == "rưỡi":
                            # Have ruoi
                            text_to_convert = text_to_convert.replace("rưỡi", "")
                            main_time = text_convert_split[idx - 1]

                            # Have PM part
                            if "chiều" in text_convert_split or "tối" in text_convert_split or "đêm" in text_convert_split:
                                if "chiều" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("chiều", "")
                                if "tối" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("tối", "")
                                if "đêm" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("đêm", "")

                                if ":" in main_time:
                                    part = main_time.split(":")[0]
                                    updated_time = str(int(part) + 12) + ":30"
                                elif main_time.isdigit():
                                    updated_time = str(int(main_time) + 12) + ":30"
                            # Have AM part
                            elif "sáng" in text_convert_split or "trưa" in text_convert_split:
                                if "sáng" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("sáng", "")
                                if "sáng" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("trưa", "")
                                if ":" in main_time:
                                    part = main_time.split(":")[0]
                                    updated_time = part + ":30"
                                elif main_time.isdigit():
                                    updated_time = main_time + ":30"
                            # Nothing
                            else:
                                if ":" in main_time:
                                    part = main_time.split(":")[0]
                                    updated_time = part + ":30"
                                elif main_time.isdigit():
                                    updated_time = main_time + ":30"
                        else:
                            # No ruoi
                            main_time = text_convert_split[idx - 1]
                            if "chiều" in text_convert_split or "tối" in text_convert_split or "đêm" in text_convert_split:
                                if "chiều" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("chiều", "")
                                if "tối" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("tối", "")
                                if "đêm" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("đêm", "")

                                if ":" in main_time:
                                    part = main_time.split(":")[0]
                                    updated_time = str(int(part) + 12) + ":00"
                                elif main_time.isdigit():
                                    updated_time = str(int(main_time) + 12) + ":00"
                            elif "sáng" in text_convert_split or "trưa" in text_convert_split:
                                if "sáng" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("sáng", "")
                                if "sáng" in text_to_convert:
                                    text_to_convert = text_to_convert.replace("trưa", "")
                                if ":" in main_time:
                                    part = main_time.split(":")[0]
                                    updated_time = part + ":00"
                                elif main_time.isdigit():
                                    updated_time = main_time + ":00"
                            else:
                                if ":" in main_time:
                                    part = main_time.split(":")[0]
                                    updated_time = part + ":00"
                                elif main_time.isdigit():
                                    updated_time = main_time + ":00"

                    else:
                        # This part to prevent bugs
                        if ":" in main_time:
                            part = main_time.split(":")[0]
                            updated_time = part + ":00"
                        elif main_time.isdigit():
                            updated_time = main_time + ":00"

                    text_to_convert = text_to_convert.replace(main_time, updated_time)
            return text_to_convert
        print("Input: ", text)
        text = textConvert(text)
        print("After textConvert: ", text)
        text = timeConvert(text)
        print("After timeConvert: ", text)
        text = changeCommandToQuestion(text)
        print("After changeCommandToQuestion: ", text)
        word_segmented_text = annotator.tokenize(text)
        word_segmented_text = word_segmented_text[0]
        for i in range(len(word_segmented_text)):
            if word_segmented_text[i] == "tàu_hoả":
                word_segmented_text[i] = "tàu_hỏa"
        print(word_segmented_text)
        # Check if given sentences have a real main verb and add it to the sentence
        addRealVerb(word_segmented_text)
        # remove useless "thành phố" verb which may cause trouble parsing
        word_segmented_text = [x for x in word_segmented_text if x != 'thành_phố']
        print("Xử lý câu tương tự để có kết quả: " + " ".join(word for word in word_segmented_text))
        return word_segmented_text

    @staticmethod
    def parsing(word_segmented_text):
        relations_set = []
        city_set = []
        connected_arc = {'từ': 0, 'đến': 0}

        with open('../Assignment/models/relations.txt', 'r') as file1:
            for line1 in file1:
                relate, left_val, right_val = line1.split()
                # print(relate, left_val, right_val)
                relations_set.append(Relation(left_val, relate, right_val))

        with open('../Assignment/models/city.txt', 'r') as file2:
            city_set = file2.read().splitlines()

        file_parsing = open("../Assignment/Output/output_a.txt", 'a')

        file_arcs = open("../Assignment/Output/output_b.txt", 'a')

        print(
            f"{'ACTION ':<25}  {'STACK':<40} {'BUFFER':<100} {'ARCS'}",
            file=file_parsing)
        sentence_conf = Configuration(['root'], word_segmented_text, []) #Stack , buffer, arc
        print(
            f"{'':<25}  {'[' + ', '.join(item for item in sentence_conf.stack) + ']':<40} {'[' + ', '.join(item for item in sentence_conf.buffer) + ']':<100} {'[' + ', '.join(str(arc) for arc in sentence_conf.arcs) + ']'}",
            file=file_parsing)
        index = 0
        while 1:
            # Begin parsing
            if len(sentence_conf.buffer) == 0:
                # Complete parsing and write to files
                print("\n", file=file_parsing)
                print(", ".join(str(arc) for arc in sentence_conf.arcs) + "\n", file=file_arcs)

                return sentence_conf.arcs
            # As of now, i should only consider on tail and head of these instance
            w_i = sentence_conf.stack[-1]
            w_j = sentence_conf.buffer[0]

            # Loop through all elements of the set to find relations
            right_rel = None
            left_rel = None
            for relation in relations_set:
                if Relation(w_i, "", w_j) == relation:
                    right_rel = relation
                    if w_i in city_set or w_i in ["lúc", "lúc_nào"] and w_j in ["từ", "đến"]:
                        right_rel = None
                    if right_rel is not None:
                        if w_i in ['từ', 'đến']:
                            connected_arc[w_i] += 1
                    break
                elif Relation(w_j, "", w_i) == relation:
                    left_rel = relation
                    # Exclude cases that this somewhat parsing the wrong order
                    # The order is like <from> <at> <to> <at>
                    if w_i in city_set or w_i in ["lúc", "lúc_nào"] and w_j in ["từ", "đến"]:
                        left_rel = None
                    if left_rel is not None:
                        if w_j in ['từ', 'đến']:
                            connected_arc[w_j] += 1
                    break
            # If there is no relation between tail and head, the buffer still have elements, shift
            if right_rel is None and left_rel is None:
                # We should check if w_j have some relationship with some elements in stack, going down from tail,
                # not including root
                have_hidden_arc = False
                for word in reversed(sentence_conf.stack[:-1]):
                    for relation in relations_set:
                        if Relation(word, "", w_j) == relation:
                            have_hidden_arc = True
                            # Check if the relation is already featured in the arcs
                            for featured in sentence_conf.arcs:
                                if Relation(word, "", w_j) == featured:
                                    have_hidden_arc = False
                            # I think most P should only have 2 connected arcs at most
                            if word in ['từ', 'đến']:
                                if connected_arc[word] >= 2:
                                    have_hidden_arc = False
                            break
                        elif Relation(w_j, "", word) == relation:
                            have_hidden_arc = True
                            for featured in sentence_conf.arcs:
                                if Relation(w_j, "", word) == featured:
                                    have_hidden_arc = False
                            if w_j in ['từ', 'đến']:
                                if connected_arc[w_j] >= 2:
                                    have_hidden_arc = False
                            break
                if have_hidden_arc:
                    # Experience-based reduce
                    Transition.reduce(sentence_conf, file_parsing)
                else:
                    Transition.shift(sentence_conf, file_parsing)

            # If there is a relation between head and tail
            if right_rel is not None:
                # This part is to solve N - N modifier in Vietnamese
                if right_rel.relation_name == "nmod":
                    Transition.right_arc_star(sentence_conf, right_rel.relation_name, file_parsing)
                else:
                    Transition.right_arc(sentence_conf, right_rel.relation_name, file_parsing)
            elif left_rel is not None:
                Transition.left_arc(sentence_conf, left_rel.relation_name, file_parsing)

    @staticmethod
    def grammar_relation(sentence_conf):
        # Create a grammar tree represent the grammatical relation of the sentence
        # Using tree for easier to create a hierarchy tree
        tree = {}
        parent_node = child_node = None
        name_parent = name_child = None

        # Words type deduction base on arcs
        for idx, rel in enumerate(sentence_conf):
            if rel.relation_name == "root":
                name_parent = rel.left
                name_child = rel.right
                parent_node = Token(name_parent, "S")
                child_node = Token(name_child, "V")
            elif rel.relation_name == "punc":
                name_parent = rel.left
                name_child = rel.right
                parent_node = Token(name_parent, "V")
                child_node = Token(name_child, "<none>")
            elif rel.relation_name == "nmod":
                name_parent = rel.left
                name_child = rel.right
                parent_node = Token(name_parent, "N")
                child_node = Token(name_child, "N")
            elif rel.relation_name in ["nsubj", "dobj"]:
                name_parent = rel.left
                name_child = rel.right
                parent_node = Token(name_parent, "V")
                child_node = Token(name_child, "N")
            elif rel.relation_name == "prep":
                name_parent = rel.left
                if rel.left == "đến":
                    name_child = rel.right + "-to"
                elif rel.left == "từ":
                    name_child = rel.right + "-from"
                elif rel.left == "hết":
                    name_child = rel.right
                parent_node = Token(name_parent, "V")
                if rel.left == "hết":
                    child_node = Token(name_child, "N")
                else:
                    child_node = Token(name_child, "P")
            elif rel.relation_name == "tmod":
                # get the closest prep, it's before the current relation
                name_child = rel.right
                if sentence_conf[idx - 1].left == "đến":
                    name_parent = rel.left + "-to"
                elif sentence_conf[idx - 1].left == "từ":
                    name_parent = rel.left + "-from"
                elif rel.left == "hết":
                    name_parent = rel.left
                parent_node = Token(name_parent, "P")
                child_node = Token(name_child, "N")
            elif rel.relation_name == "pobj":
                name_parent = rel.left
                name_child = rel.right
                parent_node = Token(name_parent, "V")
                child_node = Token(name_child, "P")
            elif rel.relation_name == "yn":
                name_parent = rel.left
                name_child = rel.right
                parent_node = Token(name_parent, "V")
                child_node = Token(name_child, "YN")

            # Add to the tree
            tree.setdefault(name_parent, parent_node)
            tree.setdefault(name_child, child_node)
            tree[name_parent].add(tree[name_child])

        # Write these to files

        file_grammar_relation = open("../Assignment/Output/output_c.txt", 'a')
        # print(tree)
        print("S root [", file=file_grammar_relation)
        print("SUBJ [" + str(tree["root"].children[0].children[0]) + "]", file=file_grammar_relation)
        print("[MAIN-" + tree["root"].children[0].type + " " + tree["root"].children[0].word + "]",
              file=file_grammar_relation)
        for i in range(1, len(tree["root"].children[0].children)):
            if str(tree["root"].children[0].children[i]) != "":
                print("[" + str(tree["root"].children[0].children[i]) + "]", file=file_grammar_relation)
        print("]", file=file_grammar_relation)

        # The main tree is this tree
        return tree["root"].children[0]

    @staticmethod
    def logical_form(grammar_relation):
        # Change to logical form
        # print(grammar_relation)
        index_type = 0
        if str(grammar_relation).find("YN") != -1:
            index_type = 1
        question_type = ["WH-QUERY", "Y/N-QUESTION", "COMMAND"]
        city_set = []
        bus_name = []
        with open('../Assignment/models/city.txt', 'r') as file1:
            city_set = file1.read().splitlines()
        with open('../Assignment/models/TrainName.txt', 'r') as file2:
            bus_name = file2.read().splitlines()

        # Atm, should only concern on WH
        log_form = {}
        log_form.setdefault(question_type[index_type], {})
        log_form[question_type[index_type]].setdefault(grammar_relation.word, {})
        agent = from_loc = to_loc = from_time = to_time = take_time = ""

        for info in grammar_relation.children:
            if info.word == "tàu_hỏa":
                agent += "<TRAIN t1 "
                if info.children:
                    for child_subj in info.children:
                        if child_subj.word == "nào":
                            agent += "<WH t1 NAME>"
                        elif child_subj.word in bus_name:
                            agent += "<NAME t1 \"" + child_subj.word + "\">"
                agent += ">"
            elif info.word == "từ":
                # If have children
                if info.children:
                    for child in info.children:
                        # if this child is a place -> city name:
                        if child.type == "N":
                            if child.word in city_set:
                                from_loc += "<CITY t1<NAME t1 " + child.word + ">>"
                            elif child.word == "đâu":
                                from_loc += "<CITY t1<WH t1 NAME>>"
                        # if this child is a preposition -> time
                        if child.type == "P":
                            if child.word == "lúc-from":
                                # get the time
                                from_time += "<TIME t1 " + child.children[0].word + ">"
                            elif child.word == "lúc_nào-from":
                                from_time += "<TIME t1 <WH t1 TIME>>"
            elif info.word == "đến":
                # If have children
                if info.children:
                    for child in info.children:
                        # if this child is a place -> city name:
                        if child.type == "N":
                            if child.word in city_set:
                                to_loc += "<CITY t1<NAME t1 " + child.word + ">>"
                            elif child.word == "đâu":
                                to_loc += "<CITY t1<WH t1 NAME>>"
                        # if this child is a preposition -> time
                        if child.type == "P":
                            if child.word == "lúc-to":
                                # get the time
                                to_time += "<TIME t1 " + child.children[0].word + ">"
                            elif child.word == "lúc_nào-to":
                                to_time += "<TIME t1 <WH t1 TIME>>"
            elif info.word == "hết":
                if info.children:
                    for child in info.children:
                        # This must be a N
                        if child.word == "bao_lâu":
                            take_time += "<TIME t1 <WH t1 TIME>>"
                        else:
                            take_time += "<TIME t1 " + child.word + ">"

        # Throw data into the dict
        if agent != "":
            log_form[question_type[index_type]][grammar_relation.word].setdefault("AGENT", agent)
        if from_loc != "":
            log_form[question_type[index_type]][grammar_relation.word].setdefault("SOURCE", from_loc)
        if from_time != "":
            log_form[question_type[index_type]][grammar_relation.word].setdefault("LEAVE", from_time)
        if to_loc != "":
            log_form[question_type[index_type]][grammar_relation.word].setdefault("DESTINATION", to_loc)
        if to_time != "":
            log_form[question_type[index_type]][grammar_relation.word].setdefault("ARRIVE", to_time)
        if take_time != "":
            log_form[question_type[index_type]][grammar_relation.word].setdefault("RUN-TIME", take_time)

        # Write to file
        file_logical_form = open("../Assignment/Output/output_d.txt", 'a')
        print(log_form, file=file_logical_form)

        return log_form

    @staticmethod
    def procedure_form(logical_form):
        # Change logical_form (as a dict) to procedure form
        procedure_str = ""
        if "WH-QUERY" in logical_form:
            procedure_str += "PRINT-ALL\n"
            # at this point, only one verb allow:
            if "chạy" in logical_form["WH-QUERY"]:
                info_dict = logical_form["WH-QUERY"]["chạy"]
                # Get as much info as possible:
                agent_query = source_query = dest_query = leave_query = arrive_query = run_time_query = ""
                for idx, key in enumerate(info_dict):
                    if key == "AGENT":
                        # Processing agent
                        agent_info = info_dict[key][:-2].split("<")[1:]
                        if "WH" in agent_info[1]:
                            # Unknown train name
                            agent_query += "?tr (TRAIN ?tr) "
                        elif "NAME" in agent_info[1]:
                            train_name = agent_info[1].split()[2][1:-1].upper()
                            agent_query += "(TRAIN " + train_name + ") "
                    elif key == "SOURCE":
                        source_info = info_dict[key][:-2].split("<")[1:]
                        if "WH" in source_info[1]:
                            # Unknow city name
                            source_query += "?dp (DTIME ?tr ?dp ?dt)"
                        else:
                            # Known city name
                            encoded_city_name = city_name_encode(source_info[1].split()[2])
                            source_query += "(DTIME ?tr " + encoded_city_name + " ?dt) "
                    elif key == "DESTINATION":
                        dest_info = info_dict[key][:-2].split("<")[1:]
                        if "WH" in dest_info[1]:
                            # Unknow city name
                            dest_query += "?ap (ATIME ?tr ?ap ?at)"
                        else:
                            encoded_city_name = city_name_encode(dest_info[1].split()[2])
                            dest_query += "(ATIME ?tr " + encoded_city_name + " ?at)"
                    elif key == "LEAVE":
                        leave_info = info_dict[key][1:-1].split()
                        if "WH" in leave_info[2]:
                            # Unknow time
                            leave_query += "?dt (DTIME ?tr ?dp ?dt)"
                        else:
                            leave_time = leave_info[2].split()[0] + "HR"
                            leave_query += "(DTIME ?tr ?dp " + leave_time + ")"
                    elif key == "ARRIVE":
                        arrive_info = info_dict[key][1:-1].split()
                        if "WH" in arrive_info[2]:
                            arrive_query += "?at (ATIME ?tr ?ap ?at)"
                        else:
                            leave_time = arrive_info[2].split()[0] + "HR"
                            arrive_query += "(ATIME ?tr ?ap " + leave_time + ")"
                    elif key == "RUN-TIME":
                        run_time_info = info_dict[key][1:-1].split()
                        if "WH" in run_time_info[2]:
                            run_time_query += "?rt (RUN-TIME ?tr ?dp ?ap ?rt)"
                        else:
                            run_time = run_time_info[2].split()[0] + "HR"
                            run_time_query += "(RUN-TIME ?tr ?dp ?ap " + run_time + ")"

                # Combine the query to get a full query
                full_source_query = full_leave_query = full_run_query = ""
                dplace_info = "?dp"
                dtime_info = "?dt"
                aplace_info = "?ap"
                atime_info = "?at"

                # First full source query -> replace ? by real info as much as possible
                if source_query == "" and leave_query != "":
                    full_source_query = leave_query
                elif source_query != "" and leave_query == "":
                    full_source_query = source_query
                elif source_query == "" and leave_query == "":
                    full_source_query = ""
                else:
                    # Get the ?info data
                    question_mark = []
                    split_source = source_query[1:-1].split()
                    split_leave = leave_query[1:-1].split()
                    if "?" in split_source[0]:
                        question_mark.append(split_source[0])
                        if "?" not in split_source[3]:
                            dplace_info = split_source[3]
                        if "?" not in split_source[4]:
                            dtime_info = split_source[4]
                    else:
                        if "?" not in split_source[2]:
                            dplace_info = split_source[2]
                        if "?" not in split_source[3]:
                            dtime_info = split_source[3]
                    if "?" in split_leave[0]:
                        question_mark.append(split_leave[0])
                        if "?" not in split_leave[3]:
                            dplace_info = split_leave[3]
                        if "?" not in split_leave[4]:
                            dtime_info = split_leave[4]
                    else:
                        if "?" not in split_leave[2]:
                            dplace_info = split_leave[2]
                        if "?" not in split_leave[3]:
                            dtime_info = split_leave[3]
                    full_source_query = " ".join(
                        x for x in question_mark) + " (DTIME ?tr " + dplace_info + " " + dtime_info
                    if full_source_query[:-1] != ")": full_source_query += ")"

                # full leave query
                if dest_query == "" and arrive_query != "":
                    full_leave_query = arrive_query
                elif dest_query != "" and arrive_query == "":
                    full_leave_query = dest_query
                elif dest_query == "" and arrive_query == "":
                    full_leave_query = ""
                else:
                    # Get the ?info data
                    question_mark = []

                    split_dest = dest_query[1:-1].split()
                    split_arrive = arrive_query[1:-1].split()
                    if "?" in split_dest[0]:
                        question_mark.append(split_dest[0])
                        if "?" not in split_dest[3]:
                            aplace_info = split_dest[3]
                        if "?" not in split_dest[4]:
                            atime_info = split_dest[4]
                    else:
                        if "?" not in split_dest[2]:
                            aplace_info = split_dest[2]
                        if "?" not in split_dest[3]:
                            atime_info = split_dest[3]
                    if "?" in split_arrive[0]:
                        question_mark.append(split_arrive[0])
                        if "?" not in split_arrive[3]:
                            aplace_info = split_arrive[3]
                        if "?" not in split_arrive[4]:
                            atime_info = split_arrive[4]
                    else:
                        if "?" not in split_arrive[2]:
                            aplace_info = split_arrive[2]
                        if "?" not in split_arrive[3]:
                            atime_info = split_arrive[3]
                    full_leave_query = " ".join(
                        x for x in question_mark) + " (ATIME ?tr " + aplace_info + " " + atime_info
                    if full_leave_query[:-1] != ")": full_leave_query += ")"

                # Get the ?dp and ?ap of the run_query
                if full_source_query != "":
                    if "?" in full_source_query.split()[0]:
                        dplace_info = full_source_query.split()[3]
                    else:
                        dplace_info = full_source_query.split()[2]
                if full_leave_query != "":
                    if "?" in full_leave_query.split()[0]:
                        aplace_info = full_leave_query.split()[3]
                    else:
                        aplace_info = full_leave_query.split()[2]
                if dplace_info != "?dp" and aplace_info != "?ap":
                    full_run_query = run_time_query.replace("?dp", dplace_info).replace("?ap", aplace_info)
                elif dplace_info == "?dp" and aplace_info != "?ap":
                    full_run_query = run_time_query.replace("?ap", aplace_info)
                elif dplace_info != "?dp" and aplace_info == "?ap":
                    full_run_query = run_time_query.replace("?dp", dplace_info)
                else:
                    full_run_query = run_time_query

                # Complete the full query and write to file
                if agent_query != "":
                    procedure_str += agent_query + "\n"
                if full_source_query != "":
                    procedure_str += full_source_query + "\n"
                if full_leave_query != "":
                    procedure_str += full_leave_query + "\n"
                if full_run_query != "":
                    procedure_str += full_run_query + "\n"

                file_procedure_form = open("../Assignment/Output/output_e.txt", 'a')
                print(procedure_str, file=file_procedure_form)
                return procedure_str
        elif "Y/N-QUESTION" in logical_form:
            procedure_str += "FIND-THE\n"
            # at this point, only one verb allow:
            if "chạy" in logical_form["Y/N-QUESTION"]:
                info_dict = logical_form["Y/N-QUESTION"]["chạy"]
                # Get as much info as possible:
                agent_query = source_query = dest_query = leave_query = arrive_query = run_time_query = ""
                for idx, key in enumerate(info_dict):
                    if key == "AGENT":
                        # Processing agent
                        agent_info = info_dict[key][:-2].split("<")[1:]
                        if "WH" in agent_info[1]:
                            # Unknown train name
                            agent_query += "?tr (TRAIN ?tr) "
                        elif "NAME" in agent_info[1]:
                            train_name = agent_info[1].split()[2][1:-1].upper()
                            agent_query += "(TRAIN " + train_name + ") "
                    elif key == "SOURCE":
                        source_info = info_dict[key][:-2].split("<")[1:]
                        if "WH" in source_info[1]:
                            # Unknow city name
                            source_query += "?dp (DTIME ?tr ?dp ?dt)"
                        else:
                            # Known city name
                            encoded_city_name = city_name_encode(source_info[1].split()[2])
                            source_query += "(DTIME ?tr " + encoded_city_name + " ?dt) "
                    elif key == "DESTINATION":
                        dest_info = info_dict[key][:-2].split("<")[1:]
                        if "WH" in dest_info[1]:
                            # Unknow city name
                            dest_query += "?ap (ATIME ?tr ?ap ?at)"
                        else:
                            encoded_city_name = city_name_encode(dest_info[1].split()[2])
                            dest_query += "(ATIME ?tr " + encoded_city_name + " ?at)"
                    elif key == "LEAVE":
                        leave_info = info_dict[key][1:-1].split()
                        if "WH" in leave_info[2]:
                            # Unknow time
                            leave_query += "?dt (DTIME ?tr ?dp ?dt)"
                        else:
                            leave_time = leave_info[2].split()[0] + "HR"
                            leave_query += "(DTIME ?tr ?dp " + leave_time + ")"
                    elif key == "ARRIVE":
                        arrive_info = info_dict[key][1:-1].split()
                        if "WH" in arrive_info[2]:
                            arrive_query += "?at (ATIME ?tr ?ap ?at)"
                        else:
                            leave_time = arrive_info[2].split()[0] + "HR"
                            arrive_query += "(ATIME ?tr ?ap " + leave_time + ")"
                    elif key == "RUN-TIME":
                        run_time_info = info_dict[key][1:-1].split()
                        if "WH" in run_time_info[2]:
                            run_time_query += "?rt (RUN-TIME ?tr ?dp ?ap ?rt)"
                        else:
                            run_time = run_time_info[2].split()[0] + "HR"
                            run_time_query += "(RUN-TIME ?tr ?dp ?ap " + run_time + ")"

                # Combine the query to get a full query
                full_source_query = full_leave_query = full_run_query = ""
                dplace_info = "?dp"
                dtime_info = "?dt"
                aplace_info = "?ap"
                atime_info = "?at"

                # First full source query -> replace ? by real info as much as possible
                if source_query == "" and leave_query != "":
                    full_source_query = leave_query
                elif source_query != "" and leave_query == "":
                    full_source_query = source_query
                elif source_query == "" and leave_query == "":
                    full_source_query = ""
                else:
                    # Get the ?info data
                    question_mark = []
                    split_source = source_query[1:-1].split()
                    split_leave = leave_query[1:-1].split()
                    if "?" in split_source[0]:
                        question_mark.append(split_source[0])
                        if "?" not in split_source[3]:
                            dplace_info = split_source[3]
                        if "?" not in split_source[4]:
                            dtime_info = split_source[4]
                    else:
                        if "?" not in split_source[2]:
                            dplace_info = split_source[2]
                        if "?" not in split_source[3]:
                            dtime_info = split_source[3]
                    if "?" in split_leave[0]:
                        question_mark.append(split_leave[0])
                        if "?" not in split_leave[3]:
                            dplace_info = split_leave[3]
                        if "?" not in split_leave[4]:
                            dtime_info = split_leave[4]
                    else:
                        if "?" not in split_leave[2]:
                            dplace_info = split_leave[2]
                        if "?" not in split_leave[3]:
                            dtime_info = split_leave[3]
                    full_source_query = " ".join(
                        x for x in question_mark) + " (DTIME ?tr " + dplace_info + " " + dtime_info
                    if full_source_query[:-1] != ")": full_source_query += ")"

                # full leave query
                if dest_query == "" and arrive_query != "":
                    full_leave_query = arrive_query
                elif dest_query != "" and arrive_query == "":
                    full_leave_query = dest_query
                elif dest_query == "" and arrive_query == "":
                    full_leave_query = ""
                else:
                    # Get the ?info data
                    question_mark = []

                    split_dest = dest_query[1:-1].split()
                    split_arrive = arrive_query[1:-1].split()
                    if "?" in split_dest[0]:
                        question_mark.append(split_dest[0])
                        if "?" not in split_dest[3]:
                            aplace_info = split_dest[3]
                        if "?" not in split_dest[4]:
                            atime_info = split_dest[4]
                    else:
                        if "?" not in split_dest[2]:
                            aplace_info = split_dest[2]
                        if "?" not in split_dest[3]:
                            atime_info = split_dest[3]
                    if "?" in split_arrive[0]:
                        question_mark.append(split_arrive[0])
                        if "?" not in split_arrive[3]:
                            aplace_info = split_arrive[3]
                        if "?" not in split_arrive[4]:
                            atime_info = split_arrive[4]
                    else:
                        if "?" not in split_arrive[2]:
                            aplace_info = split_arrive[2]
                        if "?" not in split_arrive[3]:
                            atime_info = split_arrive[3]
                    full_leave_query = " ".join(
                        x for x in question_mark) + " (ATIME ?tr " + aplace_info + " " + atime_info
                    if full_leave_query[:-1] != ")": full_leave_query += ")"

                # Get the ?dp and ?ap of the run_query
                if full_source_query != "":
                    if "?" in full_source_query.split()[0]:
                        dplace_info = full_source_query.split()[3]
                    else:
                        dplace_info = full_source_query.split()[2]
                if full_leave_query != "":
                    if "?" in full_leave_query.split()[0]:
                        aplace_info = full_leave_query.split()[3]
                    else:
                        aplace_info = full_leave_query.split()[2]
                if dplace_info != "?dp" and aplace_info != "?ap":
                    full_run_query = run_time_query.replace("?dp", dplace_info).replace("?ap", aplace_info)
                elif dplace_info == "?dp" and aplace_info != "?ap":
                    full_run_query = run_time_query.replace("?ap", aplace_info)
                elif dplace_info != "?dp" and aplace_info == "?ap":
                    full_run_query = run_time_query.replace("?dp", dplace_info)
                else:
                    full_run_query = run_time_query

                # Complete the full query and write to file
                if agent_query != "":
                    procedure_str += agent_query + "\n"
                if full_source_query != "":
                    procedure_str += full_source_query + "\n"
                if full_leave_query != "":
                    procedure_str += full_leave_query + "\n"
                if full_run_query != "":
                    procedure_str += full_run_query + "\n"
                procedure_str += "(Y/N-QUESTION)"
                file_procedure_form = open("../Assignment/Output/output_e.txt", 'a')
                print(procedure_str, file=file_procedure_form)
                return procedure_str
    @staticmethod
    def get_query_answer(query, question):
        if query.find("Y/N-QUESTION") != -1:
            # read data
            train_data = []
            atime_data = []
            dtime_data = []
            rtime_data = []
            with open('../Assignment/models/data.txt', 'r') as file:
                lines = [line.rstrip() for line in file]
                for line in lines:
                    if "TRAIN" in line:
                        train_data.append(line)
                    elif "ATIME" in line:
                        atime_data.append(line)
                    elif "DTIME" in line:
                        dtime_data.append(line)
                    elif "RUN-TIME" in line:
                        rtime_data.append(line)

            index_train = int(query.find("(TRAIN"))
            index_next = int(query.find(")", index_train))
            train_name = query[index_train + 7 : index_next]
            # print(train_name)
            thanh_pho = None
            if query.find("DTIME") != -1:
                if query.find("HN") != -1:
                    thanh_pho = "HN"
                elif query.find("HCMC") != -1:
                    thanh_pho = "HCMC"
                elif query.find("DANANG") != -1:
                    thanh_pho = "DANANG"
                elif query.find("HUE") != -1:
                    thanh_pho = "HUE"
                elif query.find("NTrang") != -1:
                    thanh_pho = "NTrang"

            result = False
            if query.find("DTIME") != -1:
                for e in dtime_data:
                    if thanh_pho != None:
                        if e.find(train_name) != -1 and e.find(thanh_pho) != -1:
                            result = True
                            break
            # print("result", result)
            result_str = result
            file_result = open("../Assignment/Output/output_f.txt", 'a')
            print("Q: " + question, file=file_result)
            print("A: " + "Đúng" if result_str else "Sai" + "\n", file=file_result)
            return result_str, None


        else:
            # read data
            train_data = []
            atime_data = []
            dtime_data = []
            rtime_data = []
            have_dtime = have_atime = have_both_da = False
            with open('../Assignment/models/data.txt', 'r') as file:
                lines = [line.rstrip() for line in file]
                for line in lines:
                    if "TRAIN" in line:
                        train_data.append(line)
                    elif "ATIME" in line:
                        atime_data.append(line)
                    elif "DTIME" in line:
                        dtime_data.append(line)
                    elif "RUN-TIME" in line:
                        rtime_data.append(line)
            commands = query.split("\n")
            # Extract bus name, city name, hour from the given data
            possible_train_name = [item[1:-1].split()[1] for item in train_data]
            possible_city_code = ['HCMC', 'HN', 'DANANG', 'HUE', 'NTrang']
            possible_atimes = [item[1:-1].split()[3] for item in atime_data]
            possible_dtimes = [item[1:-1].split()[3] for item in dtime_data]
            possible_time = list(set(possible_atimes) | set(possible_dtimes))
            possible_run_time = [item[1:-1].split()[4] for item in rtime_data]
            result = []
            for cmd in commands:
                if "DTIME" in cmd: have_dtime = True
                if "ATIME" in cmd: have_atime = True
            have_both_da = have_dtime & have_atime
            if commands[0] == "PRINT-ALL":
                # start matching
                var_to_get = []     # contain ? marks
                gotten_train = []   # contain name of the train in the queries
                result_d = []       # result collected in dtime queries
                result_a = []       # result collected in atime queries
                result_r = []       # result collected in rtime queries
                dtime_appear = atime_appear = False
                for item in commands[1:]:
                    if item != "":
                        if "?" in item.split()[0]:
                            # Have data to collect
                            question_mark = item.split()[0]
                            if question_mark == "?tr":
                                # Train name
                                # Don't know train -> add all possible train name
                                var_to_get.append(question_mark)
                                for train_item in train_data:
                                    gotten_train.append(train_item.split()[1][:-1])
                            # this query is sure to be second if exist -> only have 1 train name atm
                            if question_mark == "?dp":
                                var_to_get.append(question_mark)
                                # Replace place by place
                                for city_code in possible_city_code:
                                    # Replace train by train
                                    for train_name in gotten_train:
                                        # Prepared command
                                        check_cmd = item[4:].replace("?tr", train_name).replace("?dp", city_code).strip()
                                        have_mark_unused = False
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            if "?dt" == part:
                                                if not part in var_to_get:
                                                    # Have ? which will not be part of the result
                                                    have_mark_unused = True
                                                    break
                                        if have_mark_unused:
                                            # 100% to be ?dt -> Replace time by time
                                            for time_point in possible_time:
                                                check_cmd = item[4:].replace("?dt", time_point).replace("?tr",
                                                                                                        train_name).replace(
                                                    "?dp", city_code).strip()
                                                if check_cmd in dtime_data:
                                                    result_d.append(city_code)
                                        else:
                                            # dt known -> check normally
                                            if check_cmd in dtime_data:
                                                result_d.append(city_code)
                            if question_mark == "?ap":
                                # Same as ?dp, just change some output source
                                var_to_get.append(question_mark)
                                for city_code in possible_city_code:
                                    for train_name in gotten_train:
                                        check_cmd = item[4:].replace("?tr", train_name).replace("?ap", city_code).strip()
                                        have_mark_unused = False
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            if "?at" == part:
                                                if not part in var_to_get:
                                                    have_mark_unused = True
                                                    break
                                        if have_mark_unused:
                                            # 100% to be ?at
                                            for time_point in possible_time:
                                                check_cmd = item[4:].replace("?at", time_point).replace("?tr",
                                                                                                        train_name).replace(
                                                    "?ap", city_code).strip()
                                                if check_cmd in atime_data:
                                                    result_a.append(city_code)
                                        else:
                                            if check_cmd in dtime_data:
                                                result_a.append(city_code)
                            # Similar
                            if question_mark == "?at":
                                var_to_get.append(question_mark)
                                for time_point in possible_time:
                                    for train_name in gotten_train:
                                        check_cmd = item[4:].replace("?tr", train_name).replace("?at", time_point).strip()
                                        have_mark_unused = False
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            # 100% to be ?ap in this case
                                            if "?ap" == part:
                                                if not part in var_to_get:
                                                    have_mark_unused = True
                                                    break
                                        if have_mark_unused:
                                            # 100% to be ?ap
                                            for city_code in possible_city_code:
                                                check_cmd = item[4:].replace("?at", time_point).replace("?tr",
                                                                                                        train_name).replace(
                                                    "?ap", city_code).strip()
                                                if check_cmd in atime_data:
                                                    result_a.append(time_point)
                                        else:
                                            if check_cmd in atime_data:
                                                result_a.append(time_point)
                            if question_mark == "?dt":
                                var_to_get.append(question_mark)
                                for time_point in possible_time:
                                    for train_name in gotten_train:
                                        check_cmd = item[4:].replace("?tr", train_name).replace("?dt", time_point).strip()
                                        have_mark_unused = False
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            # 100% to be ?dp in this case
                                            if "?dp" == part:
                                                if not part in var_to_get:
                                                    have_mark_unused = True
                                                    break
                                        if have_mark_unused:
                                            # 100% to be ?ap
                                            for city_code in possible_city_code:
                                                check_cmd = item[4:].replace("?dt", time_point).replace("?tr",
                                                                                                        train_name).replace(
                                                    "?dp", city_code).strip()
                                                if check_cmd in dtime_data:
                                                    result_d.append(time_point)
                                        else:
                                            if check_cmd in dtime_data:
                                                result_d.append(time_point)
                            # A little differences, not much though, process almost the same
                            if question_mark == "?rt":
                                var_to_get.append(question_mark)
                                for run_time_test in possible_run_time:
                                    for train_name in gotten_train:
                                        check_cmd = item[4:].replace("?tr", train_name).replace("?rt",
                                                                                                run_time_test).strip()
                                        have_mark_unused = False
                                        list_unused = []
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            # May be ?dp or ?ap -> Place
                                            if part in ["?ap", "?dp"]:
                                                if not part in var_to_get:
                                                    have_mark_unused = True
                                                    list_unused.append(part)
                                        if have_mark_unused:
                                            # don't know either cities
                                            if len(list_unused) == 2:
                                                for citi1 in possible_city_code:
                                                    for citi2 in possible_city_code:
                                                        check_cmd = item[4:].replace("?tr", train_name).replace("?rt",
                                                                                                                run_time_test).replace(
                                                            list_unused[0], citi1).replace(list_unused[1], citi2).strip()
                                                        if check_cmd in rtime_data:
                                                            result_r.append(run_time_test)
                                            # know one
                                            elif len(list_unused) == 1:
                                                for citi1 in possible_city_code:
                                                    check_cmd = item[4:].replace("?tr", train_name).replace("?rt",
                                                                                                            run_time_test).replace(
                                                        list_unused[0], citi1).strip()
                                                if check_cmd in rtime_data:
                                                    result_r.append(run_time_test)
                                        else:
                                            # know all
                                            if check_cmd in rtime_data:
                                                result_r.append(run_time_test)
                        else:
                            # Train name is provided
                            if item.split()[1][:-1] in possible_train_name:
                                gotten_train.append(item.split()[1][:-1])
                            elif gotten_train:
                                for train_name in gotten_train:
                                    # Replace ?tr in 2 command by train_name
                                    check_cmd = item.replace("?tr", train_name).strip()
                                    have_mark_unused = False
                                    unused_part = ""
                                    # Check dtime condition
                                    if "DTIME" in check_cmd:
                                        dtime_appear = True
                                        # print(check_cmd)

                                        # Check if there is ? in the command
                                        # Remove the parenthesis
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            if "?" in part:
                                                # Check if not part is in var_to_get
                                                if not part in var_to_get:
                                                    have_mark_unused = True
                                                    unused_part = part
                                                    break
                                        if have_mark_unused:
                                            # Don't care this in the command -> Make it available for all possible values
                                            if unused_part == "?dp":
                                                for citi in possible_city_code:
                                                    check_cmd = item.replace("?dp", citi).replace("?tr", train_name).strip()
                                                    if check_cmd in dtime_data:
                                                        result_d.append(train_name)
                                            elif unused_part == "?dt":
                                                for time_point in possible_time:
                                                    check_cmd = item.replace("?dt", time_point).replace("?tr",
                                                                                                        train_name).strip()
                                                    if check_cmd in dtime_data:
                                                        result_d.append(train_name)
                                        else:
                                            if check_cmd in dtime_data:
                                                result_d.append(train_name)
                                    elif "ATIME" in check_cmd:
                                        atime_appear = True
                                        parts_check_cmd = check_cmd[1:-1].split()
                                        for part in parts_check_cmd:
                                            if "?" in part:
                                                # Check if not part is in var_to_get
                                                if not part in var_to_get:
                                                    have_mark_unused = True
                                                    unused_part = part
                                                    break
                                        if have_mark_unused:
                                            # Don't care this in the command -> Make it available for all possible values
                                            if unused_part == "?ap":
                                                for citi in possible_city_code:
                                                    check_cmd = item.replace("?ap", citi).replace("?tr", train_name).strip()
                                                    if check_cmd in atime_data:
                                                        result_a.append(train_name)
                                            elif unused_part == "?at":
                                                for time_point in possible_time:
                                                    check_cmd = item.replace("?at", time_point).replace("?tr",
                                                                                                        train_name).strip()
                                                    if check_cmd in atime_data:
                                                        result_a.append(train_name)
                                        else:
                                            if check_cmd in atime_data:
                                                result_a.append(train_name)

                # Intersection if ?tr is to find
                if "?tr" in var_to_get:
                    if dtime_appear and atime_appear:
                        result = list(set(result_a) & set(result_d))
                    elif not dtime_appear and atime_appear:
                        result = result_a
                    elif dtime_appear and not atime_appear:
                        result = result_d
                # ?dp is union
                elif "?dp" in var_to_get or "?ap" in var_to_get:
                    result = result_d + result_a
                # ?t is consider by time, if both dtime and atime appears, one of the result have none -> truncate both
                # Else result be one of them
                elif "?dt" in var_to_get or "?at" in var_to_get:
                    if "?dt" in var_to_get:
                        if "?at" in var_to_get:
                            result = result_d + result_a
                        else:
                            # Check if both of the command appear
                            if have_both_da:
                                if result_a:
                                    result = result_d + result_a
                                else:
                                    result = []
                            else:
                                result = result_d
                    elif "?at" in var_to_get:
                        if "?dt" in var_to_get:
                            result = result_d + result_a
                        else:
                            if have_both_da:
                                if result_d:
                                    result = result_d + result_a
                                else:
                                    result = []
                            else:
                                result = result_a
                elif "?rt" in var_to_get:
                    result = result_r

            # Decode the city name if any
            for idx, item in enumerate(result):
                if item in possible_city_code:
                    result[idx] = city_name_decode(item)

            # index_train = int(query.find("(TRAIN"))
            # index_next = int(query.find(")", index_train))
            # train_name = query[index_train + 7: index_next]
            # # print(train_name)
            # thanh_pho = None
            # if query.find("DTIME") != -1:
            #     if query.find("HN") != -1:
            #         thanh_pho = "HN"
            #     elif query.find("HCMC") != -1:
            #         thanh_pho = "HCMC"
            #     elif query.find("DANANG") != -1:
            #         thanh_pho = "DANANG"
            #     elif query.find("HUE") != -1:
            #         thanh_pho = "HUE"
            #     elif query.find("NTrang") != -1:
            #         thanh_pho = "NTrang"
            #
            # lst_train = []
            # if train_name.find("?") != -1 and thanh_pho != None:
            #     if query.find("DTIME") != -1:
            #         for e in dtime_data:
            #             train, tp = e.split(" ")[1:3]
            #             if thanh_pho == tp:
            #                 lst_train.append(train)
            # print(lst_train)

            # Write to file
            result_str = ""
            if result:
                result_str += "Kết quả là " + ",".join(res for res in result) + "."
            else:
                result_str += "Không có kết quả thoả mãn."

            file_result = open("../Assignment/Output/output_f.txt", 'a')
            print("Q: " + question, file=file_result)
            print("A: " + result_str + "\n", file=file_result)
            return result_str, result


def process(text):
    two_question_time = False
    index = text.find(',')
    if index != -1:
        two_question_time = True

    if not two_question_time:
        preprocessed_text = ProcessText.preprocessing(text)
        word_relation = ProcessText.parsing(preprocessed_text)
        grammar_rel = ProcessText.grammar_relation(word_relation)
        log_form = ProcessText.logical_form(grammar_rel)
        query_str = ProcessText.procedure_form(log_form)
        answer = ProcessText.get_query_answer(query_str, text)
        return answer
    else:
        ques_1 = text[0: index] + "?"
        preprocessed_text = ProcessText.preprocessing(ques_1)
        word_relation = ProcessText.parsing(preprocessed_text)
        grammar_rel = ProcessText.grammar_relation(word_relation)
        log_form = ProcessText.logical_form(grammar_rel)
        query_str = ProcessText.procedure_form(log_form)
        answer, ret = ProcessText.get_query_answer(query_str, ques_1)

        # train_name = answer.split(" ")[-1][:-1]
        train_data = []
        atime_data = []
        dtime_data = []
        rtime_data = []
        with open('../Assignment/models/data.txt', 'r') as file:
            lines = [line.rstrip() for line in file]
            for line in lines:
                if "TRAIN" in line:
                    train_data.append(line)
                elif "ATIME" in line:
                    atime_data.append(line)
                elif "DTIME" in line:
                    dtime_data.append(line)
                elif "RUN-TIME" in line:
                    rtime_data.append(line)

        answer = "Kết quả là "
        if query_str.find("DTIME"):
            for e in dtime_data:
                _split = e.split(" ")
                train, time = _split[1], _split[3][:-1]
                if train in ret:
                    answer += train
                    answer += " - "
                    answer += time
                    answer += "; "
        with open('../Assignment/Output/output_f.txt', 'w') as file:
            print("Q: " + text, file=file)
            print("A: " + answer, file=file)
        return answer