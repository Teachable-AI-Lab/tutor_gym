from abc import ABCMeta, abstractmethod
from typing import Any
from tutorgym.utils import unique_hash
import sys
import os
import glob


class Annotatable:
    def add_annotations(self, annos):
        self.annotations = {**self.annotations, **annos}

    def remove_annotations(self, anno_keys):
        self.annotations = {k:v for k, v in self.annotations.items() if k not in annos}

    def get_annotation(self, key, *args, **kwargs):
        return self.annotations.get(key, *args, **kwargs)


# ----------------------------------
# : ProblemState

class ProblemState(Annotatable):
    def __new__(cls, objs, action_hist=[], **annotations):
        if(isinstance(objs, ProblemState)):
            return objs
        self = super().__new__(cls)
        self.objs = objs
        self.annotations = annotations
        self.action_hist = action_hist
        # self.memset = ms_builder(objs)
        # self._uid = f"S_{self.memset.long_hash()}"
        return self

    def __getitem__(self, attr):
        return self.objs[attr]

    def __setitem__(self, attr, val):
        if(self.objs.get(attr,None) != val):
            self._longhash = None #Invalidate longhash on change
        self.objs[attr] = val

    def copy(self, add_hist=None, keep_annotations=True):
        objs_copy = {k : {**v} for k,v in self.objs.items()}

        annotations_copy = {}
        if(isinstance(keep_annotations, bool)):
            if(keep_annotations == True):
                annotations_copy = {k:v for k,v in self.annotations.items()}
        else:
            annotations_copy = {k:v for k,v in self.annotations.items() if k in keep_annotations}
        
        if(add_hist is not None):
            hist_copy = [*self.action_hist, add_hist]
        else:
            hist_copy = [*self.action_hist]
        ps = ProblemState(objs_copy, hist_copy, **annotations_copy)
        return ps

    def __copy__(self):
        return self.copy()

    @property
    def longhash(self):
        if(getattr(self, '_longhash', None) is None):
            # Note: Slow-ish way to update modifications via rebuilding
            # self.memset = self.ms_builder(self.objs)
            sorted_state = sorted(self.objs.items())
            self._longhash = self._longhash = f"S_{unique_hash(sorted_state)}"
        return self._longhash

    @property
    def unique_id(self):
        if("unique_id" in self.annotations):
            return self.annotations["unique_id"]
        else:
            return self.longhash
        

    def __eq__(self, other):
        # NOTE: uids long/hash-conflict safe so this should be fine
        return self.longhash == other.longhash

    def __hash__(self):
        return hash(self.longhash)

    def __str__(self):
        return f"ProblemState_{self.longhash[:8]}"

    def __repr__(self):
        s = f"ProblemState_{self.longhash[:8]}({self.objs}" + \
               f", action_hist=[{self.action_hist}])"
        for anno_name, anno in self.annotations.items():
            s += f", {anno_name}={anno!r}"
        s += ")"
        return s

    def get(self, *args, **kwargs):
        return self.objs.get(*args, **kwargs)

    def items(self):
        return self.objs.items()

        

# ----------------------------------
# : Registries 


action_translator_registry = {} 
def register_action_translator(_type):
    ''' Register a function for translating a user defined action
        type into a standard Action. 
    
    Example Usage:
        @register_action_translator(MyCustomActionType)
        def my_translator(my_obj):
            sai = (my_obj.selection, my_obj.action_type, my_obj.inputs) 
            return Action(sai, args=my_obj.args)
    '''
    def wrapper(func):
        action_translator_registry[_type] = func        
        return func

    return wrapper


annotation_equal_registry = {} 
def register_annotation_equal(anno_name):
    ''' Register a special __equal__ implementation for a
        particular annotation kind. 

        Example Usage
        @register_annotation_equal("args")
        def unordered_equals(args1, args2):
            ...
            return sorted(args1) == sorted(args2)
    '''

    def wrapper(func):
        annotation_equal_registry[anno_name] = func
        return func
    return wrapper


# ----------------------------------
# : Action


def _standardize_action(val):
    if(isinstance(val, (list,tuple))):
        selection, action_type, inp = val
        annotations = {}
    elif(isinstance(val, dict)):
        selection = val['selection']
        action_type = val.get('action_type', val.get('action'))
        if(action_type is None):
            raise KeyError("'action_type' | 'action'")

        inp = val.get('input', None)
        if(inp is None):
            inputs = getattr(val, 'inputs', None)
            if(inputs):
                inp = inputs['value']
        annotations = {k:v for k,v in val.items() if k not in ("selection", "action_type", "action", "inputs", "input")}

    elif(hasattr(val, 'selection')):
        selection = val.selection
        action_type = getattr(val, 'action_type', None)
        if(action_type is None):
            action_type = getattr(val, 'action', None)

        inp = getattr(val, 'input', None)
        if(inp is None):
            inputs = getattr(val, 'inputs', None)
            if(inputs):
                inp = inputs['value']


        annotations = {k:v for k,v in val.__dict__.items() if k not in ("selection", "action_type", "action", "inputs", "input")}
    else:
        raise ValueError(f"Unable to translate {val} to Action.")

    return (selection, action_type, inp), annotations

# Note: this is a strict interface 
class ActionLike(metaclass=ABCMeta): 
    selection : str
    action_type : str
    input : Any
    slots = ('selection', 'action_type', 'input')

    def __init__(self, *args, **kwargs):
        (sel, at, inp), _ = _standardize_action(*args)
        self.selection = sel
        self.action_type = at
        self.input = inp

    @abstractmethod
    def as_tuple(self):
        return (self.selection, self.action_type, self.input)


class Action(ActionLike, Annotatable):
    ''' An object representing the ideal action taken by an agent.
        Includes Selection-ActionType-Inputs (SAI) and optional annotations 
        like the string of the how-part of the skill that produced the SAI
        and the arguments it used to produce the action.
    '''
    selection : str
    action_type : str
    input : Any
    annotations : dict[str, Any]
    slots = ('selection', 'action_type', 'input', 'annotations')

    def __init__(self, *args, **kwargs):
        pass

    def __new__(cls, *args, **annotations):

        if(len(args) == 3):
            obj = (*args,)
        else:
            obj = args[0]

        # If get an Action then make a copy
        if(isinstance(obj, Action)):
            self = super().__new__(cls)
            self.selection = obj.selection
            self.action_type = obj.action_type
            self.input = obj.input
            self.annotations = {**obj.annotations, **annotations}
        else:
            # If get a type with an action translator then make from that
            translator = action_translator_registry.get(type(obj), None)
            if(translator):
                # print("TRANSLATE!", sai)
                self = translator(obj)
                self.annotations = {**self.annotations, **annotations}

            # Otherwise try from a 
            else:
                self = super().__new__(cls)
                (sel, at, inp), obj_annos = _standardize_action(obj)
                self.selection = sel
                self.action_type = at
                self.input = inp
                self.annotations = {**obj_annos, **annotations}

        return self



    def is_equal(self, other, check_annotations=[]):        
        if(self.as_tuple() != other.as_tuple()):
            return False

        for anno in check_annotations:
            # self_has = anno in self.annotations
            # other_has = anno in other.annotations
            # # print("has", self_has, other_has)
            # if(self_has != other_has):
            #     return False

            # if(not self_has):
            #     continue

            self_anno = self.annotations.get(anno, None)
            other_anno = other.annotations.get(anno, None)

            eq = annotation_equal_registry.get(anno, None)

            if(eq is not None):
                if(not eq(self_anno, other_anno)):
                    return False
            else:
                if(self_anno != other_anno):
                    return False

        return True


    def __eq__(self, other):
        return self.is_equal(other)

    def check(self, state, other):
        checker = self.annotations.get("checker", None)
        if(checker is not None):
            return checker(state, other) 
        else:
            return self.as_tuple() == other.as_tuple()

    def __hash__(self):
        return hash((unique_hash(self.as_tuple()), unique_hash(self.annotations)))

    def __str__(self):
        return f"{self.action_type}({self.selection}, {self.input})"

    def __repr__(self):
        s = f"{self.action_type}({self.selection}, {self.input})"

        for anno_name, anno in self.annotations.items():
            s += f", {anno_name}={anno!r}"
        return s + ")"

    def copy(self, omit_annotations=[]):
        new_annos = {k:v for k,v in self.annotations.items() if k not in omit_annotations}
        return Action(self.as_tuple(), **new_annos)

    def __copy__(self):
        return self.copy()

    # TODO: Remove this?
    def as_train_kwargs(self):
        return {
            "action" : self,
            **self.annotations,
            }

    def get_info(self):
        return {
            "selection" : self.selection,
            "action_type" : self.action_type,
            "input" : self.input,
            **self.annotations,
        }

    def as_tuple(self):
        return (self.selection, self.action_type, self.input)


# -------------------------------------------------------
# : glob_iter

def glob_iter(**kwargs):
    # Python < 3.10 no support for glob(root_dir=...) (need to hack it)
    if(sys.version_info < (3, 10)):
        root_dir = kwargs.get("root_dir", "./")
        if("root_dir" in kwargs):
            kwargs = {k:v for k,v in kwargs.items() if k != "root_dir"}
        kwargs['pathname'] = os.path.join(root_dir, kwargs['pathname'])
        results = glob.glob(**kwargs)
        results = [os.path.relpath(x, root_dir) for x in results]
        return results

    # Python >= 3.10 supports glob(root_dir=...)
    else:
        return glob.glob(**kwargs)
