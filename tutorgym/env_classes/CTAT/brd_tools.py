import xmltodict
import lxml.etree as ET
from tutorgym.shared import Action

# --------------------
# : parse_sai

def parse_sai(node):
    selection = node.find("Selection").find("value").text
    action_type = node.find("Action").find("value").text
    inputs = {}
    for node in node.find("Input"):
        inputs[node.tag] = node.text

    return Action((selection, action_type, inputs))


# --------------------
# : parse_start_node_messages()

def parse_jess_wm_description(node):
    # Probably don't need to implement this, but it is a thing
    #  in the brds I have
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

def parse_edge(edge):
    # for edge in edges:

    # -- SAI Part --
    action_label = edge.find("actionLabel")
    message = action_label.find("message")

    verb = message.find("verb").text
    if(verb != "NotePropertySet"):
        if(verbosity > 0):
            print(f"Warning edge message unknown verb: {verb}")
    properties = message.find("properties")
    if(properties.find("MessageType").text != "InterfaceAction"):
        raise ValueError(f"unexpected edge MessageType: {properties.find('MessageType').text}")
    action = parse_sai(properties)

    # -- Annotations --
    annotations = {}
    bm = action_label.find("buggyMessage")
    if(bm is not None):
        annotations["buggy_message"] = bm.text

    sm = action_label.find("successMessage")
    if(sm is not None):
        annotations["success_message"] = bm.text

    hint_messages = []
    for hint in action_label.iter("hintMessage"):
        hint_messages.append(hint.text)

    annotations["hint_messages"] = hint_messages
    action.add_annotations(annotations)

    src_id = edge.find("sourceID").text
    dest_id = edge.find("destID").text
    return (src_id, dest_id, action)



def parse_brd(filepath):
    start_actions = None
    edges = []

    tree = ET.parse(filepath)
    root = tree.getroot()
    for child in root:

        if(child.tag == "startNodeMessages"):
            problem_name, start_actions = parse_start_node_messages(child)

        elif(child.tag == "edge"):
            edges.append(parse_edge(child))


    print(problem_name)
    print("--START ACTIONS--")
    for a in start_actions:
        print(a)
    print("--EDGES--")
    for e in edges:
        print(e)

    return start_actions, edges

        # print("  ", child, child.tag)

# parse_brd("AS_3_7_plus_4_7.brd")
# parse_brd("Mathtutor/6_01_HTML/FinalBRDs/Problem1.brd")


