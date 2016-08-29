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
{readerValues}
public:
   {className}(TTree* tree): fTreeReader(tree){initCode} {{}};
   Bool_t Next(){{return fTreeReader.Next();}}
{getterMethods}
}};
#endif
'''

_class_code_cache_template = '''
#ifndef __{className}__
#define __{className}__

class {className} {{
private:
{dataVectors}
   unsigned long int fIndex;
   unsigned long int fNEntries;
public:
   {className}(TTree* tree):fIndex(-1){{
        TTreeReader fTreeReader(tree);
        fNEntries = fTreeReader.GetEntries(true);

{dataVectorsInit}

{readerValues}

      while(fTreeReader.Next()) {{
{dataVectorsFill}
      }}
   }}
{getterMethods}
   Bool_t Next(){{auto cont = fNEntries > ++fIndex; fIndex = cont? fIndex : -1; return cont; }}

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

def _get_class_code_cached(branchesNameTypes, theclassname):
    '''Create the class code, cache the data'''
    the_data_vectors = ''
    the_TTreeReaderValues = ''
    data_vectors_fill = ''
    data_vectors_init = ''
    the_getters = ''
    for name, typeName in branchesNameTypes:
        cppname = _get_cpp_branch_name(name)
        readerName = '%s_reader' %cppname
        vectorName = 'f%s' %cppname
        vectorType = 'std::vector<%s>' %typeName
        the_TTreeReaderValues += '   TTreeReaderValue<%s> %s(fTreeReader, "%s");\n' %(typeName, readerName, name)
        the_data_vectors +=  '   %s %s;\n' %(vectorType, vectorName)
        data_vectors_init += '      %s.reserve(fNEntries);\n' %vectorName;
        data_vectors_fill += '          %s.emplace_back(*%s);\n' %(vectorName,readerName)
        the_getters += '   const %s& %s_array(){return %s;}\n' %(vectorType,cppname, vectorName)
        the_getters += '   const %s& %s(){return %s[fIndex];}\n' %(typeName,cppname, vectorName)
    return _class_code_cache_template.format(className = theclassname,
                                       readerValues = the_TTreeReaderValues,
                                       dataVectors = the_data_vectors,
                                       dataVectorsInit = data_vectors_init,
                                       dataVectorsFill = data_vectors_fill,
                                       getterMethods = the_getters)

def _get_class_code(branchesNameTypes, theclassname):
    '''Create the class code'''
    thegetters = ''
    thettreeReaderValues = ''
    theInit = ''
    # Here the loop on branches and creation of data members and getters
    for name, typeName in branchesNameTypes:
        cppname = _get_cpp_branch_name(name)
        memberName = 'f%s' %cppname
        thettreeReaderValues += '   TTreeReaderValue<%s> %s;\n' %(typeName,memberName)
        theInit += ',\n                          %s(fTreeReader, "%s")' %(memberName,name)
        thegetters += '   const %s& %s(){return *%s;}\n' %(typeName,cppname,memberName) 
    return _class_code_template.format(className = theclassname, 
                                       readerValues = thettreeReaderValues,
                                       initCode = theInit,
                                       getterMethods = thegetters)

class PyTreeReader:
    def __init__(self, tree, pattern='*', branchList=None, cache=False):
        curFile = tree.GetCurrentFile()
        if curFile:
            filename = curFile.GetName()
        else:
           ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(6))
        theclassname = "cl_%s" %abs(hash(filename+tree.GetName()+pattern+str(branchList)+str(cache)))
        if branchList:
            filter_func = lambda branch: branch.GetName() in branchList
        else:
            filter_func = lambda branch: fnmatch(branch.GetName(), pattern)
        branches = [branch for branch in tree.GetListOfBranches() if filter_func(branch)]
        branchesNameTypes = _get_branch_names_types(branches)
        if cache:
            classCode = _get_class_code_cached(branchesNameTypes, theclassname)
        else:
            classCode = _get_class_code(branchesNameTypes, theclassname)
        #print classCode
        # Here some caching? Is it worth?
        if not hasattr(ROOT, theclassname):
            ROOT.gInterpreter.Declare(classCode)
        self._ttreeReaderWrapper = getattr(ROOT, theclassname)(tree)
        self._next = self._ttreeReaderWrapper.Next

        # Expose arrays
        if cache:
            for name,_ in branchesNameTypes:
                methodName = name+'_array'
                setattr(self, methodName, getattr(self._ttreeReaderWrapper,methodName)) 

    def __iter__(self):
        while self._next():
            yield self._ttreeReaderWrapper
