from tutorgym.shared import Action, ProblemState

# ------------------------------------------------------------------
# : CTAT_ActionModel

class CTAT_ActionModel:
    @classmethod
    def apply(self, state, action, is_correct=True, make_copy=True):
        state = ProblemState(state)
        if(make_copy):
            new_state = state.copy(add_hist=action, keep_annotations=False)
        else:
            new_state = state
            new_state.action_hist.append(action)

        sel, act_type, inp = action.as_tuple()

        # print(sel, act_type, inputs)

        # Handle 'done' first since it often isn't named in the HTML
        if(act_type == "ButtonPressed"):
            if(sel == "done"):
                # print("DONE!")
                new_state = ProblemState({}, is_done=True)

            # Pressing a button might do nothing
            else:
                pass
            return new_state

        try:
            sel_obj = new_state[sel]
        except Exception as e:

            # print("EXCEPTION", e)
            # if(sel == "done"):
            #     print(repr(new_state))
            #     raise e;
            return new_state



        if(act_type in ("UpdateTextArea", "UpdateTextField")):
            sel_obj['value'] = inp
            sel_obj['locked'] = True
        elif(act_type == "SetDisplay"):
            sel_obj['display'] = inp

        return new_state
