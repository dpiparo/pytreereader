'''
A class to loop on TTrees, fast.
The key idea consists in exploiting the ROOT interpreter to build a loop in C++ rather than in Python.
Author: Danilo Piparo 2016
'''

import ROOT
import random
import string
from fnmatch import fnmatch

'''
The template code for the class used to loop over the events.
'''
_class_code_template = '''
#ifndef __{className}__
#define __{className}__

class {className} {{
private:
   TTreeReader fTreeReader;
{dataMembers}
public:
   {className}(TTree* tree): fTreeReader(tree){initCode} {{}};
   Bool_t Next(){{return fTreeReader.Next();}}
{getterMethods}
}};
#endif
'''

def _get_branch_type_name(branch):
    '''Get the name of the branch type, being it a class or a pod.'''
    typeName = branch.GetClassName()
    if '' == typeName:
        typeName = branch.GetListOfLeaves()[0].GetTypeName()
    return typeName

def _get_cpp_branch_name(branchName):
    '''Transform branch names in C++ names'''
    if branchName.endswith('.'): branchName = branchName[:-1]
    return branchName.replace(' ','_')

def _get_branch_names_types(branches):
    branchesNameTypes = [(b.GetName(),_get_branch_type_name(b)) for b in branches]
    return branchesNameTypes

def _get_class_code(branches, theclassname):
    '''Create the class code'''
    thegetters = ""
    thettreeReaderValues = ""
    theInit = ""
    branchesNameTypes = _get_branch_names_types(branches)
    # Here the loop on branches and creation of data members and getters
    for name, typeName in branchesNameTypes:
        cppname = _get_cpp_branch_name(name)
        memberName = 'f%s' %cppname
        thettreeReaderValues += '   TTreeReaderValue<%s> %s;\n' %(typeName,memberName)
        theInit += ',\n                          %s(fTreeReader, "%s")' %(memberName,name)
        thegetters += '   const %s& %s(){return *%s;}\n' %(typeName,cppname,memberName) 
    return _class_code_template.format(className = theclassname, 
                                       dataMembers = thettreeReaderValues,
                                       initCode = theInit,
                                       getterMethods = thegetters)

class PyTreeReader:
    def __init__(self, tree, pattern='*', branchList=None):
        curFile = tree.GetCurrentFile()
        filename = curFile.GetName() if curFile else ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(6))
        theclassname = "cl_%s" %abs(hash(filename+tree.GetName()))
        if branchList:
            filter_func = lambda branch: branch.GetName() in branchList
        else:
            filter_func = lambda branch: fnmatch(branch.GetName(), pattern)
        branches = [branch for branch in tree.GetListOfBranches() if filter_func(branch)]
        classCode = _get_class_code(branches, theclassname)
        # Here some caching? Is it worth?
        if not hasattr(ROOT, theclassname):
            ROOT.gInterpreter.Declare(classCode)
        self._ttreeReaderWrapper = getattr(ROOT, theclassname)(tree)
        self._next = _ttreeReaderWrapper.Next()

    def __iter__(self):
        while self.next():
            yield self._ttreeReaderWrapper
