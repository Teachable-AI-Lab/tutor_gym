from apprentice.agents.cre_agents.cre_agent import SkillApplication
from tutorgym.shared import register_action_translator, register_annotation_equal, Action

@register_action_translator(SkillApplication)
def SkillApp_to_Action(skill_app):
    # print("TRANSL:", hasattr(skill_app, "match"), hasattr(skill_app, "match"))

    annotations = {}
    if(hasattr(skill_app, "match")):
        arg_foci = [x if isinstance(x,str) else x.id for x in skill_app.match[1:]]
        annotations["arg_foci"] = arg_foci;

    how_str = getattr(skill_app, 'how_str', None)
    if(how_str is None):
        skill = getattr(skill_app, 'skill', None)
        func = getattr(skill, 'how_part', None)
        how_str = str(func) 
    annotations['how_str'] = how_str;

    # print(annotations)

    return Action(skill_app.action.as_tuple(), **annotations)

@register_annotation_equal("arg_foci")
def args_unordered_equals(args1, args2):
    if(args1 is None): args1 = []
    if(args2 is None): args2 = []        
    srt_args1 = tuple(sorted([x if isinstance(x,str) else x.id for x in args1]))
    srt_args2 = tuple(sorted([x if isinstance(x,str) else x.id for x in args2]))
    return srt_args1 == srt_args2
