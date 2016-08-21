'''
A class to loop on TTrees, fast.
Author: Danilo Piparo 2016
'''

import ROOT

_class_code_template = '''
class %s {
private:
   TTreeReader fTreeReader;
%s
public:
   %s(TTree* tree): fTreeReader(tree)%s {};
   Bool_t Next(){return fTreeReader.Next();}
%s
};
'''

def _get_branch_type_name(branch):
    '''Get the name of the branch type, being it a class or a pod.'''
    typeName = branch.GetClassName()
    if '' == typeName:
        typeName = branch.GetListOfLeaves()[0].GetTypeName()
    return typeName

class PyTreeReader:
    def __init__(self, tree, pattern="", regex="", branchList=[]):
        _pyReaderCounter = 0
        theclassname = "class_%s" %_pyReaderCounter

        thegetters = ""
        thettreeReaderValues = ""
        theInit = ""
        # Here the loop on branches and creation of data members and getters
        branchesNameTypes = [(b.GetName(),_get_branch_type_name(b)) for b in tree.GetListOfBranches()]
        for name, typeName in branchesNameTypes:
            memberName = 'f%s' %name
            thettreeReaderValues += '   TTreeReaderValue<%s> %s;\n' %(typeName,memberName)
            theInit += ',\n                          %s(fTreeReader, "%s")' %(memberName,name)
            thegetters += '   const %s& %s(){return *f%s;}\n' %(typeName,name,name) 
        classCode = _class_code_template %(theclassname, thettreeReaderValues,theclassname, theInit, thegetters)
        #print classCode
        ROOT.gInterpreter.Declare(classCode)
        self._ttreeReaderWrapper = getattr(ROOT, theclassname)(tree)
    def __iter__(self):
        while self._ttreeReaderWrapper.Next():
            yield self._ttreeReaderWrapper
