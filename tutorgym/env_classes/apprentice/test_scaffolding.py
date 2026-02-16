"""Scaffold testing framework."""

from tutorgym.env_classes.apprentice.apprentice_tutor import ApprenticeTutor


class ScaffoldIterator:
    
    @staticmethod
    def get_scaffolds_for_domain(domain, initial_problem):
        """Get available scaffolds for a domain."""
        try:
            # Create a temporary environment to call get_available_scaffolds()
            env = ApprenticeTutor(domain=domain, initial_problem=initial_problem, scaffold="first")
            return env.get_available_scaffolds()
        except Exception as e:
            # If anything goes wrong print warning
            print(f"Warning: Could not detect scaffolds for {domain}")
            return ["all", None]
    
    @staticmethod
    def get_scaffold_name(scaffold):
        """Get human-readable name for scaffold level"""
        if scaffold == "all":
            return "Full Scaffolding"
        elif scaffold is None:
            return "No Scaffolding"
        else:
            return f"Scaffold {scaffold.replace('level_', '')}"


def test_scaffold_level(domain, initial_problem, scaffold_level):
    """Creates an environment at a specific scaffold level and measures the initial state."""
    # Initialize the environment at the requested scaffold level
    # Note scaffold="all" must be set after initialization, so using "first" as a placeholder
    env = ApprenticeTutor(
        domain=domain,
        initial_problem=initial_problem,
        scaffold=scaffold_level if scaffold_level != "all" else "first"
    )
    
    if scaffold_level == "all":
        env.scaffold = "all"
    
    state = env.get_state()
    
    # Count input fields (exclude label fields and the equation display)
    num_fields = len([k for k in state.objs.keys() if 'label' not in k and k != 'equation'])
    
    # Count how many fields are already locked
    locked_fields = len([v for v in state.objs.values() if v.get('locked', False)])
    
    return {
        "scaffold_level": scaffold_level,
        "problem": env.get_problem(),
        "num_fields": num_fields,
        "locked_fields": locked_fields,
    }


def run_baseline_tests(domain, initial_problem):
    """Tests the same problem at every available scaffold level and return results"""
    scaffolds = ScaffoldIterator.get_scaffolds_for_domain(domain, initial_problem)
    results = []
    
    for scaffold in scaffolds:
        try:
            result = test_scaffold_level(domain, initial_problem, scaffold)
            results.append(result)
        except Exception as e:
            results.append({"scaffold_level": scaffold, "error": str(e)})
    
    return results