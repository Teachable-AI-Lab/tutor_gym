import xmltodict
import lxml.etree as ET
from tutorgym.shared import Action
from tutorgym.env_classes.fsm_tutor import ActionGroup

# ---------------------
class BaseMatcher:
    def __str__(self):
        return f"{type(self).__name__}({', '.join([f'{k}={v}' for k,v in self.__dict__.items()])})"

class ExpressionMatcher(BaseMatcher):
    def __init__(self, InputExpression, relation, **kwargs):
        self.value = InputExpression
        self.relation = relation
        self.kwargs = kwargs

    def check(self, state, inputs):
        # TODO actually make work
        return inputs.get('value',None) == self.value


class ExactMatcher(BaseMatcher): 
    def __init__(self, single):
        self.value = single

    def check(self, state, inputs):
        return inputs.get('value',None) == self.value

class RegexMatcher(BaseMatcher): 
    def __init__(self, single, **kwargs):
        self.value = single

    def check(self, state, inputs):
        # TODO actually make work
        return inputs.get('value',None) == self.value


matcher_classes = {
    "ExpressionMatcher" : ExpressionMatcher,
    "ExactMatcher" : ExactMatcher,
    "RegexMatcher" : RegexMatcher
}

class Checker():
    def __init__(self, selection, action_type, inputs_matcher):
        self.selection = selection
        self.action_type = action_type
        self.inputs_matcher = inputs_matcher

    def __call__(self, state, action):
        sel, act, inps = action.sai
        if(sel == self.selection and
           act == self.action_type and
           self.inputs_matcher.check(state, inps)):
            return True
        return False

    def __str__(self):
        return f"Checker({self.inputs_matcher})"

    __repr__ = __str__


# --------------------
# : parse_sai / matcher

def parse_sai(node):
    selection = node.find("Selection").find("value").text
    action_type = node.find("Action").find("value").text
    inputs = {}
    for node in node.find("Input"):
        inputs[node.tag] = node.text

    return Action((selection, action_type, inputs))

def parse_matcher(node):
    matcher_type = node.find("matcherType").text
    cls = matcher_classes[matcher_type]
    params = {x.attrib['name'] : x.text for x in node.iter("matcherParameter")}
    matcher = cls(**params)
    return matcher

# def make_checker(selection, action_type, inp_m):
#     def checker(state, action):
#             sel, act, inps = action.sai
#             if(sel == selection and
#                act == action_type and
#                inp_m.check(state, inps)):
#                 return True
#             return False
#     return checker


def parse_old_matcher(node):
    matcher_type = node.find("matcherType").text
    cls = matcher_classes[matcher_type]

    params = {x.attrib['name'] : x.text for x in node.iter("matcherParameter")}

    selection = params["selection"]
    action_type = params["action"]
    inputs = {"value" : params["input"]}
    actor = params["actor"].lower()

    inp_m = cls(params["input"])

    annotations = {"checker" : 
        Checker(selection, action_type, inp_m)
    }
    return actor, Action((selection, action_type, inputs), **annotations)



def parse_matchers(node):
    sel_m = parse_matcher(node.find("Selection").find("matcher"))
    act_m = parse_matcher(node.find("Action").find("matcher"))
    inp_m = parse_matcher(node.find("Input").find("matcher"))

    # assert isinstance(sel_m, ExactMatcher), "Not Implemented non exact 'selection' matcher"
    # assert isinstance(act_m, ExactMatcher), "Not Implemented non exact action_type matcher"

    selection = sel_m.value
    action_type = act_m.value
    inputs = {"value" : inp_m.value}

    actor = node.find("Actor").text.lower()
    # selection = node.find("Selection").find("matcher").text
    # action_type = node.find("Action").find("value").text
    # inputs = {}
    # for node in node.find("Input"):
    #     inputs[node.tag] = node.text

    annotations = {}
    if(not isinstance(inp_m, ExactMatcher)):
        annotations['checker'] = Checker(selection, action_type, inp_m)

    return actor, Action((selection, action_type, inputs), **annotations)


# --------------------
# : parse_start_node_messages()

def parse_jess_wm_description(node):
    # Probably don't need to implement this, but it is a thing
    #  in the brds of Mathtutor
    pass


def parse_start_node_messages(messages, verbosity=1):
    problem_name = None
    start_actions = []

    for message in messages:
        if(message.tag != "message"):
            if(verbosity > 0):
                print(f"Warning StartNodeMessages contains non-message: {message}")
            continue

        verb = message.find("verb").text
        if(verb == "SendNoteProperty"):
            properties = message.find("properties")
            message_type = properties.find("MessageType").text

            # StartProblem
            if(message_type == "StartProblem"):
                problem_name = properties.find("ProblemName").text

            # Jess Stuff
            elif(message_type == "InterfaceDescription"):
                parse_jess_wm_description(properties)

        elif(verb == "NotePropertySet"):
            properties = message.find("properties")
            message_type = properties.find("MessageType").text

            # InterfaceAction
            if(message_type == "InterfaceAction"):
                action = parse_sai(properties)
                start_actions.append(action)

        else:
            if(verbosity > 0):
                print(f"Warning unhandled verb: {verb}")
            
        # print("M", message, message.find("verb"))
    return problem_name, start_actions


# --------------------
# : parse_edges()

def parse_edge(edge, verbosity=1):
    # for edge in edges:

    # -- SAI Part --
    action_label = edge.find("actionLabel")
    message = action_label.find("message")

    verb = message.find("verb").text
    if(verb not in ("NotePropertySet", "SendNoteProperty")):
        if(verbosity > 0):
            print(f"Warning edge message unknown verb: {verb}")
    properties = message.find("properties")

    message_type = properties.find("MessageType").text
    if(message_type not in ["InterfaceAction", "CorrectAction"]):
        raise ValueError(f"unexpected edge MessageType: {properties.find('MessageType').text}")

    # TODO... not sure what 
    message_action = parse_sai(properties)

    
    matchers = action_label.find("matchers")
    if(matchers is not None):
        actor, matcher_action = parse_matchers(matchers)
    else:
        matcher = action_label.find("matcher")
        actor, matcher_action = parse_old_matcher(matcher)
    # print("matchers", matchers)

    # Use the matcher action instaed of the message action
    action = matcher_action
    # print("action", action)

        

    # -- Annotations --
    annotations = {"actor" : actor,
        "optional" : action_label.attrib['minTraversals'] == "0",
        **matcher_action.annotations}

    bm = action_label.find("buggyMessage")
    if(bm is not None):
        annotations["buggy_message"] = bm.text

    sm = action_label.find("successMessage")
    if(sm is not None):
        annotations["success_message"] = sm.text

    act_t = action_label.find("actionType")
    if(act_t is not None):
        annotations["action_type"] = act_t.text

    uid = action_label.find("uniqueID")
    if(uid is not None):
        annotations["unique_id"] = uid.text

    src_id = edge.find("sourceID").text
    annotations["src_id"] = src_id
    dest_id = edge.find("destID").text
    annotations["dest_id"] = dest_id

    hint_messages = []
    for hint in action_label.iter("hintMessage"):
        if(hint.text):
            hint_messages.append(hint.text)

    annotations["hint_messages"] = hint_messages
    action.add_annotations(annotations)

    # print(f"{repr(action)}")
    
    return (src_id, dest_id, action)


# --------------------
# : parse_group()

def parse_groups(edge_groups, edges):
    out_groups = {}
    for i, group_node in enumerate(edge_groups.iter("group")):
        name = group_node.attrib.get("name", f'group{i}')
        assert name not in out_groups, f"Duplicate EdgeGroup name {name}"

        actions = []
        for link_node in group_node.iter("link"):
            s, n, action = edges[link_node.attrib['id']]
            action.add_annotations({"group" : name})
            actions.append(action)

        unordered = group_node.attrib.get("ordered", 'false') != 'false'
        reenterable = group_node.attrib.get("reenterable", True)

        out_groups[name] = ActionGroup(name, actions, unordered, reenterable)

    return out_groups


def parse_brd(filepath, verbosity=1):
    start_actions = None
    edges = {}
    _eg_nodes = []
    edge_groups = {}

    tree = ET.parse(filepath)
    root = tree.getroot()

    try:
        for child in root:
            if(child.tag == "startNodeMessages"):
                problem_name, start_actions = parse_start_node_messages(child)

            elif(child.tag == "edge"):
                edge = (src,dest,action) = parse_edge(child, verbosity)
                edges[action.get_annotation('unique_id')] = edge
            elif(child.tag == "EdgesGroups"):
                _eg_nodes.append(child)

        # Need be parsed after edges
        for eg_node in _eg_nodes:
            edge_groups.update(parse_groups(eg_node, edges))

    except Exception as e:
        raise type(e)(f"An error occured while parsing {filepath} " + str(e)) from e


    # print(problem_name)
    # print("--START ACTIONS--")
    # for a in start_actions:
    #     print(a)
    # print("--EDGES--")
    # for e in edges:
    #     print(e)

    return start_actions, edges, edge_groups

        # print("  ", child, child.tag)

# parse_brd("AS_3_7_plus_4_7.brd")
# parse_brd("Mathtutor/6_01_HTML/FinalBRDs/Problem1.brd")


