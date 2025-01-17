from tutorgym.utils import unique_hash

# ----------------------------------
# : ProblemState
class ProblemState:
    # Global factory for MemSet Objects (w/ defualt context)
    # ms_builder = MemSetBuilder()

    def __new__(cls, objs):
        if(isinstance(objs, ProblemState)):
            return objs
        self = super().__new__(cls)
        self.objs = objs
        # self.memset = ms_builder(objs)
        # self._uid = f"S_{self.memset.long_hash()}"
        return self

    def __getitem__(self, attr):
        return self.objs[attr]

    def __setitem__(self, attr, val):
        if(self.objs.get(attr,None) != val):
            self._uid = None #Invalidate uid on change
        self.objs[attr] = val

    def copy(self):
        objs_copy = {k : {**v} for k,v in self.objs.items()}
        ps = ProblemState(objs_copy)
        return ps

    def __copy__(self):
        return self.copy()

    @property
    def uid(self):
        if(getattr(self, '_uid', None) is None):
            # Note: Slow-ish way to update modifications via rebuilding
            # self.memset = self.ms_builder(self.objs)
            sorted_state = sorted(self.objs.items())
            self._uid = self._uid = f"S_{unique_hash(sorted_state)}"
        return self._uid
        

    def __eq__(self, other):
        # NOTE: uids long/hash-conflict safe so this should be fine
        return self.uid == other.uid

    def __hash__(self):
        return hash(self.uid)

    def __str__(self):
        return self.uid[:8]

    def __repr__(self):
        return self.uid[:8]

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


def _standardize_action(inp): 
    if(isinstance(inp, (list,tuple))):
        selection, action_type, inputs = inp
        annotations = {}
    elif(isinstance(inp, dict)):
        selection = inp['selection']
        action_type = inp.get('action_type', inp.get('action'))
        if(action_type is None):
            raise KeyError("'action_type' | 'action'")
        inputs = inp['inputs']
        annotations = {k:v for k,v in inp.items() if k not in ("selection", "action_type", "action", "inputs")}

    elif(hasattr(inp, 'selection')):
        selection = inp.selection
        action_type = getattr(inp, 'action_type', None)
        if(action_type is None):
            action_type = getattr(inp, 'action', None)
        inputs = inp.inputs

        annotations = {k:v for k,v in inp.__dict__.items() if k not in ("selection", "action_type", "action", "inputs")}
    else:
        raise ValueError(f"Unable to translate {inp} to Action.")

    return (selection, action_type, inputs), annotations


class Action:
    ''' An object representing the ideal action taken by an agent.
        Includes Selection-ActionType-Inputs (SAI) and optional annotations 
        like the string of the how-part of the skill that produced the SAI
        and the arguments it used to produce the action.
    '''
    def __new__(cls, sai, **annotations):        
        # If get an Action then make a copy
        if(isinstance(sai, Action)):
            self = super().__new__(cls)
            self.sai = sai.sai
            self.annotations = {**sai.annotations, **annotations}
        
        else:
            # If get a type with an action translator then make from that
            translator = action_translator_registry.get(type(sai), None)
            if(translator):
                # print("TRANSLATE!", sai)
                self = translator(sai)
                self.annotations = {**self.annotations, **annotations}
                # print("AANNO!?", self.annotations)

            else:
                self = super().__new__(cls)
                self.sai, obj_annos = _standardize_action(sai)
                self.annotations = {**obj_annos, **annotations}


        return self

    def is_equal(self, other, check_annotations=[]):        
        if(self.sai != other.sai):
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

    def __hash__(self):
        return hash((unique_hash(self.sai), unique_hash(self.annotations)))

    def __str__(self):
        return f"{self.sai[0]}->{self.sai[2]['value']}"

    def __repr__(self):
        s = f"{self.sai[1]}({self.sai[0]}, {self.sai[2]}"

        for anno_name, anno in self.annotations.items():
            s += f", {anno_name}={anno}"
        return s + ")"

    def copy(self, omit_annotations=[]):
        sai = self.sai
        # args = self.args if not omit_args else None
        # how_str = self.how_str if not omit_how else None
        new_annos = {k:v for k,v in self.annotations.items() if k not in omit_annotations}
        return Action(sai, **new_annos)

    def __copy__(self):
        return self.copy()

    def as_train_kwargs(self):
        return {
            "sai" : self.sai,
            **self.annotations,
            }

    def get_info(self):
        return {
            "selection" : self.sai[0],
            "action_type" : self.sai[1],
            "inputs" : self.sai[2],
            **self.annotations,
        }
