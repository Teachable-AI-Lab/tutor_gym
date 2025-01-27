from tutorgym.shared import glob_iter
import os
import glob
import lxml.etree as ET


class CTATProblemSet():
    def __init__(self, name, label, problems, package_dir, problem_infos, asset_infos, **kwargs):
        self.name = name
        self.label = label
        self.problems = problems
        self.package_dir = package_dir
        self.problem_infos = problem_infos
        self.extra_info = kwargs

        self.probinfo_seq = []
        for name in self.problems:
            prob_info = self.problem_infos[name]

            html = prob_info["student_interface"]
            html_dir = asset_infos[html].get('path', "HTML")
            model = prob_info["model_file"]
            model_dir = asset_infos[model].get('path', "FinalBRDs")
            self.probinfo_seq.append({
                "html_path" : os.path.join(package_dir, html_dir, html),
                "model_path" : os.path.join(package_dir, model_dir, model),
                **prob_info
            })

    def __str__(self):
        return f"CTATProblemSet(name={self.name}, n_problems={len(self)})"

    def __len__(self):
        return len(self.problems)

    def __iter__(self):
        return iter(self.probinfo_seq)


# -------------------------------------------
# : Parsing utilities

def collect_CTAT_problem_sets(directory):
    # problems = {}
    problem_sets = []
    package_paths = sorted(collect_CTAT_packages(directory))
    for package_path in package_paths:
        _problem_sets = parse_package(package_path)
        for ps in _problem_sets:
            # problem_sets[package_dirname](ps)
            problem_sets.append(ps)
        # problems.update(prob_dicts)
        # problem_sets.update(ps_dicts)
    return problem_sets

def collect_CTAT_packages(directory):
    packages = []

    path = os.path.abspath(os.path.join(directory, "**/package.xml"))
    for package in glob_iter(pathname=path,
                             recursive=True):
        print(": ", package)
        packages.append(package)
    return packages
        
def parse_problem(problem):
    prob_dict = {**problem.attrib}
    skills = {}
    for skill in problem.find("Skills"):
        skills[skill.get("name")] = skill.attrib
    prob_dict['skills'] = skills
    return prob_dict


def parse_problem_set(problem_set):
    problems = []
    for problem in problem_set.find("Problems"):
        problems.append(problem.get("name"))

    skills = {}
    for skill in problem_set.find("Skills"):
        skills[skill.get("name")] = skill.attrib

    return {"problems" : problems, "skills" : skills, **problem_set.attrib}

def parse_package(filepath):
    
    package_dir = os.path.dirname(filepath)
    problem_sets = []


    tree = ET.parse(filepath)
    root = tree.getroot()

    for package in root.iter("Package"):
        package_name = package.get("label")

        problem_infos = {}
        asset_infos = {}
        for problem in package.find("Problems").iter("Problem"):
            prob_info = parse_problem(problem)
            problem_infos[prob_info['name']] = prob_info

        for asset in package.find("Assets").iter("Asset"):
            asset_infos[asset.get("name")] = asset.attrib

            # elif(child.tag == "ProblemSets"):
        for problem_set in package.find("ProblemSets").iter("ProblemSet"):
            ps_dict = parse_problem_set(problem_set)
            ps = CTATProblemSet(**ps_dict, 
                package_dir=package_dir,
                problem_infos=problem_infos,
                asset_infos=asset_infos)
            problem_sets.append(ps)

    return problem_sets


if __name__ == '__main__':
    problem_sets = collect_CTAT_problem_sets("../../envs/CTAT/Mathtutor/")

    # for name,prob in problems.items():
    #     print(name, ":", prob)

    for prob_set in problem_sets:
        print(f"-- {prob_set.name} --")
        for problem in prob_set:

            print("html_path:", problem['html_path'])
            print("model_path:", problem['model_path'])


