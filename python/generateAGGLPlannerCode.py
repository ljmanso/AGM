from operator import *
import collections, sys

sys.path.append('/usr/local/share/agm/')

from AGGL import *
from xmlModelParser import *

#COPY_OPTION = "kkdeepcopy"
COPY_OPTION = "copy.deepcopy"
#COPY_OPTION = "copy.copy"
#debug = True
debug = False
scorePerContition = 100


## Returns the necessary header of the python version of a grammar
# @ingroup AGGLGeneration
def constantHeader():
	return """import copy, sys, cPickle
sys.path.append('/usr/local/share/agm/')
from AGGL import *
from agglplanner import *

def getNewIdForSymbol(node):
	m = 1
	for k in node.graph.nodes:
			if int(node.graph.nodes[k].name) >= m:
				m = int(node.graph.nodes[k].name)+1
	return m

lastNodeId = 0

class RuleSet(object):
	def __init__(self):
		object.__init__(self)

# Up to this point, all the code has been generated by the generateAGGLPlanerCode.py file

"""

## This is the declaration of the first method in the grammar.py file. This method receives as input parameter:
# @ingroup AGGLGeneration
# @parameter agm The grammar
#
# @retval the string with the grammar's code
def ruleDeclaration(agm):
	# We write the name os the first method, getRules and
	# make the mapping of the dictionary of
	ret = """\tdef getRules(self):
		mapping = dict()"""

	# TO MAKE THE FILE WITH THE ACTIVES GRAMMAR RULES...
	# We look for all the grammar rules. If is an active rule
	# we take the name of the rule and took hold in the mapping variable.
	for r in agm.rules:
		if not r.passive:
			ret += "\n		mapping['"+ r.name + "'] = self." + r.name
	ret += "\n		return mapping\n\n"
	return ret

## This is the declaration of the getTriggers method in the grammar.py file. This method receives as input parameter:
# @ingroup AGGLGeneration
# @param agm The grammar
#
# @retval the string with the grammar's code
def ruleTriggerDeclaration(agm):
	ret = """\tdef getTriggers(self):
		mapping = dict()"""
	# We write all the names of the trigger that we need after
	# for the active grammar rules.
	for r in agm.rules:
		if not r.passive:
			ret += "\n		mapping['"+ r.name + "'] = self." + r.name + "_trigger"
	ret += "\n		return mapping\n\n"
	return ret

# These are the first three methods of the file that has the active grammar rules -- active.py --

## This method creates the part of the code that define the links
# @ingroup AGGLGeneration
#
# @param linkList list of all the connection betwen two symbol
# @param newSymbol the symbol that is comparing the link
# @param alreadyThere
# @param debug flag to display additional information
#
# @retval A tuple containing:
# - the string with the code
# - the number of links processed
# - the debugging code
def extractNewLinkConditionsFromList(linkList, newSymbol, alreadyThere, debug=False):
	ret = ''
	info = []
	number = 0
	for link in linkList:
		if newSymbol == link.a or newSymbol == link.b:
			pre = ' and '
			negated = ''
			if not link.enabled:
				pre += 'not '
				negated = 'not '
			if newSymbol == link.a:
				if link.b in alreadyThere:
					ret += pre + '[n2id["'+str(link.a) + '"],n2id["'+ str(link.b) + '"],"'+str(link.linkType)+'"] in snode.graph.links'
					if debug: info.append('print "'+str(link.a)+'---['+negated+str(link.linkType)+']--->'+str(link.b)+'", '+negated+'[n2id["'+str(link.a) + '"],n2id["'+ str(link.b) + '"],"'+str(link.linkType)+'"] in snode.graph.links')
					number += 1
			elif newSymbol == link.b:
				if link.a in alreadyThere:
					ret += pre + '[n2id["'+str(link.a) + '"],n2id["'+ str(link.b) + '"],"'+str(link.linkType)+'"] in snode.graph.links'
					if debug: info.append('print "'+str(link.a)+'---['+negated+str(link.linkType)+']--->'+str(link.b)+'", '+negated+'[n2id["'+str(link.a) + '"],n2id["'+ str(link.b) + '"],"'+str(link.linkType)+'"] in snode.graph.links')
					number += 1
	return ret, number, info

## This creates de heuristic of a link
#
# @ingroup AGGLGeneration
#
# @param linkList list of all the connection betwen two symbol
# @param newSymbol the symbol that is comparing the link.	 #
# @param alreadyThere
#
# @retval the string with the code
def newLinkScore(linkList, newSymbol, alreadyThere):
	ret = []
	for link in linkList:
		if newSymbol == link.a or newSymbol == link.b:
			# Adapt to negated links
			if not link.enabled: negated = 'not'
			else: negated = ''
			# Condition itself
			if ((newSymbol == link.a) and (link.b in alreadyThere)) or ((newSymbol == link.b) and (link.a in alreadyThere)):
				ret.append('if [n2id["'+str(link.a)+'"],n2id["'+str(link.b)+'"],"'+str(link.linkType)+'"] ' +negated+'in graph.links: linksVal += 100')
	return ret


## This method calls the corresponding generator for a rule (normal or combo)
#
# @ingroup AGGLGeneration
#
# @param rule the rule taken as input
#
# @retval the string with the code
#
def ruleImplementation(rule):
	# We dont work with passive rules.
	if rule.passive: return ''
	ret = ''
	indent = "\n\t"  # tabulation
	ret += indent+"# Rule " + rule.name
	# We distinguish between normal rules and combo rules.
	if type(rule) == AGMRule:
		print rule.name, 'normal'
		ret += normalRuleImplementation(rule, indent, thisIsActuallyAHierarchicalRule=False)
	elif type(rule) == AGMComboRule:
		print rule.name, 'combo'
		ret += comboRuleImplementation(rule, indent, thisIsActuallyAHierarchicalRule=False)
	elif type(rule) == AGMHierarchicalRule:
		print rule.name, 'hierarchical'
		ret += normalRuleImplementation(rule, indent, thisIsActuallyAHierarchicalRule=True)
		ret += comboRuleImplementation(rule, indent, thisIsActuallyAHierarchicalRule=True)
	else:
		print 'Unknown rule type'
		sys.exit(-2346)
	return ret

## This method generates the code for a combo rule
#
# @ingroup AGGLGeneration
#
# @param rule the current combo rule
# @param indent
#
# @retval the string with the code
def comboRuleImplementation(rule, indent, thisIsActuallyAHierarchicalRule=False):
	ret = ''
	if thisIsActuallyAHierarchicalRule: comboInside = "_COMBOINSIDE"
	else: comboInside = ''
	ret += indent+"def " + rule.name + comboInside + "(self, snode, stackP=None, equivalencesP=None):"
	indent += "\t"
	ret += indent+"if stackP == None: stackP=[]"
	ret += indent+"if equivalencesP == None: equivalencesP=[]"
	ret += indent+"stack        = "+COPY_OPTION+"(stackP)"
	ret += indent+"equivalences = "+COPY_OPTION+"(equivalencesP)"
	ret += indent+"return self." + rule.name + comboInside + "_trigger(snode, dict(), stack, equivalences)"
	ret += indent
	ret += "\n"

	indent = "\n\t"
	ret += indent+"# Rule " + rule.name
	ret += indent+"def " + rule.name + comboInside + "_trigger(self, snode, n2id, stack=None, equivalences=None, checked=True, finish=''):"
	indent += "\t"
	ret += indent+"if stack == None: stack=[]"
	ret += indent+"if equivalences == None: equivalences=[]"
	ret += indent+"aliasDict = dict()"
	ret += indent+"sid = str(len(stack)+"+str(len(rule.atoms))+")"
	ret += indent+"inCombo = (len(stack) > 0)"
	#ret += indent+"stack = "+COPY_OPTION+"(stack)"
	#ret += indent+"equivalences = "+COPY_OPTION+"(equivalences)"
	ret += indent+"for atom in ["
	a_n = 0
	for a in reversed(rule.atoms):
		if a_n == 0:
			ret += "['"+a[0]+"','"+a[1]+"', '"+"# ENDS COMBO:"+rule.name+"_'+sid], "
		else:
			ret += "['"+a[0]+"','"+a[1]+"'], "
		a_n += 1
	ret = ret[:-2]
	ret += ']:'
	indent += "\t"
	ret += indent+'idInStack = len(stack)'
	ret += indent+'if len(atom)<3:'
	ret += indent+'\tstack.append((idInStack, atom[0]))'
	ret += indent+'else:'
	ret += indent+'\tstack.append((idInStack, atom[0], atom[2]))'
	ret += indent+'aliasDict[atom[1]] = idInStack'
	indent = indent[:-1]
	ret += indent+'for equivalence in ' + str(rule.equivalences) + ':'
	indent += "\t"
	ret += indent+'equivList = []'
	ret += indent+'for similar in equivalence:'
	indent += "\t"
	ret += indent+'equivList.append([aliasDict[similar[0]], similar[1]])'
	indent = indent[:-1]
	ret += indent+'equivalences.append([equivList, None])'
	indent = indent[:-1]
	#ret += indent+'print "Current stack:", stack'
	#ret += indent+'print stack[-1]'
	#ret += indent+'print stack[-1][0]'

	ret += indent+"newNode = WorldStateHistory(snode)"
	#ret += indent+"newNode.depth -= 1 + " + str(len(rule.atoms))
	ret += indent+"global lastNodeId"
	ret += indent+"lastNodeId += 1"
	ret += indent+"if not inCombo:"
	ret += indent+"\tnewNode.cost += " + str(rule.cost)
	ret += indent+"newNode.depth += 1"
	ret += indent+"newNode.nodeId = lastNodeId"
	#ret += indent+"newNode.parentId = snode.nodeId"
	#if debug:
		#ret += indent+"print ' ------- Created', newNode.nodeId, 'from', newNode.parentId, 'rule', '" + rule.name + "'"
	ret += indent+"newNode.history.append('# STARTS COMBO:"+rule.name+"_' + sid)"
	#ret += indent+"print 'Calling ', stack[-1][1]"
	ret += indent+'ret = self.getRules()[stack[-1][1]](newNode, stack, equivalences)'
	ret += indent+"return ret"

	ret += "\n"
	ret += "\n"
	return ret

## This method generates the code for a NORMAL rule
#
# @ingroup AGGLGeneration
#
# @param the rule
# @param indent
#
# @retval the string with the code
def normalRuleImplementation(rule, indent, thisIsActuallyAHierarchicalRule=False):
	ret = ''
	# Quantifier-related code (PARAMETERS)
	# <<<
	nodesPlusParameters = rule.lhs.nodes
	if len(rule.parameters.strip()) > 0:
		for i in rule.parametersAST:
			nodesPlusParameters[i[0]] = AGMSymbol(i[0], i[1])
	# >>>
	ret += indent+"def " + rule.name + "(self, snode, stackP=None, equivalencesP=None):"
	indent += "\t"
	ret += indent+"if stackP == None: stackP=[]"
	ret += indent+"if equivalencesP == None: equivalencesP=[]"
	ret += indent + "stack        = "+COPY_OPTION+"(stackP)"
	ret += indent + "equivalences = "+COPY_OPTION+"(equivalencesP)"
	ret += indent + "symbol_nodes_copy = "+COPY_OPTION+"(snode.graph.nodes)"
	ret += indent + "finishesCombo = ''"
	#ret += indent+"stack = "+COPY_OPTION+"(stack)"
	#ret += indent+"equivalences = "+COPY_OPTION+"(equivalences)"
	ret += indent+"if len(stack) > 0:"
	indent += "\t"
	ret += indent+"inCombo = True"
	ret += indent+"pop = stack.pop()"
	ret += indent+"me = pop[0]"
	ret += indent+"if len(pop)>2:"
	ret += indent+"\tfinishesCombo = "+COPY_OPTION+"(pop[2])"
	#ret += indent+"\tsnode.history.append('<'+finishesCombo)"
	ret += indent+"\tfina = "+COPY_OPTION+"(pop[2])"

	if debug:
		#ret += indent+"print snode.nodeId, 'from', snode.parentId"
		ret += indent+"print 'Depth: ', snode.depth"
		ret += indent+"print '"+rule.name+"', me"
		ret += indent+"print stack"
		ret += indent+"print equivalences"
		ret += indent+"print '"+rule.name+"', me"
	for n in nodesPlusParameters:
		ret += indent+"# Find equivalence for "+n
		ret += indent+"symbol_"+n+"_nodes = symbol_nodes_copy"
		ret += indent+"for equiv in equivalences:"
		indent += "\t"
		ret += indent+"if [me, '"+n+"'] in equiv[0] and equiv[1] != None:"
		indent += "\t"
		#ret += indent+"print 'got "+n+" from equivalences!!'"
		ret += indent+"symbol_"+n+"_nodes = [equiv[1]]"
		indent = indent[:-2]
	indent = indent[:-1]
	if len(nodesPlusParameters)>0:
		#print rule.name, len(nodesPlusParameters)
		ret += indent+"else:"
		indent += "\t"
		ret += indent+"inCombo = False"
		for n in nodesPlusParameters:
			ret += indent+"symbol_"+n+"_nodes = symbol_nodes_copy"
		indent = indent[:-1]
	ret += indent+"ret = []"
	# Make a copy of the current graph node list
	ret += indent+"nodes = "+COPY_OPTION+"(snode.graph.nodes)"
	ret += indent+"n2id = dict()"
	## Generate Link list
	linkList = []
	for link_i in range(len(rule.lhs.links)):
		link = rule.lhs.links[link_i]
		linkList.append([link.a, link.b, link.linkType])
	linkList = sorted(linkList, key=itemgetter(0, 1, 2))
	#ret += indent+"links = [ "
	#for link_i in range(len(linkList)):
		#link = linkList[link_i]
		#if link_i > 0:
			#ret += ", "
		#ret += "['" + link[0] + "', '" + link[1] + "', '" + link[2] + "']"
	#ret += " ]"
	# Compute the not-actually-optimal order TODO improve this!
	counter = dict()
	for n in nodesPlusParameters:
		counter[n] = 0
	for n in nodesPlusParameters:
		for link in linkList:
			if n == link[0]:
				counter[n] = counter[n] + 2
			if n == link[1]:
				counter[n] = counter[n] + 1
	optimal_node_list_t = []
	for n in counter.keys():
		optimal_node_list_t.append((counter[n], n))
	optimal_node_list_t = sorted(optimal_node_list_t, reverse=True)
	optimal_node_list = []
	for o in optimal_node_list_t:
		optimal_node_list.append(o[1])
	# Generate the loop that perform the instantiation
	symbols_in_stack = []
	for n in optimal_node_list:
		ret += indent+"for symbol_"+n+"_name in symbol_"+n+"_nodes:"
		indent += "\t"
		ret += indent+"symbol_"+n+" = nodes[symbol_"+n+"_name]"
		ret += indent+"n2id['"+n+"'] = symbol_"+n+"_name"
		ret += indent+"if symbol_"+n+".sType == '"+nodesPlusParameters[n].sType+"'"
		for other in symbols_in_stack:
			ret += " and symbol_"+n+".name!=symbol_" + str(other) + ".name"
		conditions, number, ll = extractNewLinkConditionsFromList(rule.lhs.links, n, symbols_in_stack)
		ret += conditions
		ret += ":"
		symbols_in_stack.append(n)
		indent += "\t"
	# Quantifier-related code (PRECONDITION)
	# <<<
	if rule.preconditionAST != None:
		indentP = indent
		preconditionCode, indent, conditionId, stuff = normalRuleImplementation_PRECONDITION(rule.preconditionAST, indent)
		ret += indentP+'backVars = n2id.keys()'
		ret += preconditionCode
		ret += indentP+'for k in n2id.keys():'
		ret += indentP+'\tif not k in backVars:'
		ret += indentP+'\t\tdel n2id[k]'
		ret += indentP+'if precondition'+str(conditionId)+':'
		indent += '\t'
	# >>>
	# Code to call rule execution
	ret += indent+"# At this point we meet all the conditions."
	#ret += indent+"print 'Running rule "+rule.name+"'"
	ret += indent+"stack2        = "+COPY_OPTION+"(stack)"
	ret += indent+"equivalences2 = "+COPY_OPTION+"(equivalences)"
	ret += indent+"r1 = self."+rule.name+"_trigger(snode, n2id, stack2, inCombo, equivalences2, "+COPY_OPTION+"(finishesCombo))"
	ret += indent+"c = "+COPY_OPTION+"(r1)"
	ret += indent+"if 'fina' in locals():"
	ret += indent+"\tc.history.append(finishesCombo)"
	ret += indent+"if len(stack2) > 0: c.stop = True"
	ret += indent+"ret.append(c)"
	ret += indent+"if len(stack2) > 0:"
	indent += "\t"
	#ret += indent+"print '"+rule.name+" with stack'"
	#ret += indent+"equiv_deriv = "+COPY_OPTION+"(equivalences)"

	for n in optimal_node_list:
		ret += indent+"# Set symbol for "+n+"..."
		ret += indent+"for equiv in equivalences2:"
		indent += "\t"
		ret += indent+"if [me, '"+n+"'] in equiv[0]:"
		indent += "\t"
		ret += indent+"equiv[1] = symbol_"+n+"_name"
		#ret += indent+"print 'setting equivalence for " + n + "'"
		indent = indent[:-2]

	#ret += indent+"print 'Current stack2:', stack2"
	#ret += indent+"print 'Current equivs2:', equivalences2"
	#ret += indent+"print stack2[-1]"
	#ret += indent+"print stack2[-1][0]"
	ret += indent+"newNode = WorldStateHistory(r1)"
	ret += indent+"global lastNodeId"
	ret += indent+"lastNodeId += 1"
	ret += indent+"newNode.nodeId = lastNodeId"
	#ret += indent+"newNode.parentId = snode.nodeId"
	#if debug:
		#ret += indent+"print ' ------- Created', newNode.nodeId, 'from', newNode.parentId, 'rule', '"+rule.name+"'"
	ret += indent+"derivsx = self.getRules()[stack2[-1][1]](newNode, stack2, equivalences2)"
	ret += indent+"if 'fina' in locals():"
	ret += indent+"\tfor n in derivsx: n.history.append(finishesCombo)"
	ret += indent+"\tfor n in derivsx: n.history.append(fina)"
	ret += indent+"ret.extend(derivsx)"
	indent = indent[:-2]
	# Rule ending
	indent = "\n\t\t"
	if debug:
		ret += indent+"if len(ret) == 0: print snode.nodeId, '-> " + rule.name + " was a dead end'"
	ret += indent+"return ret"
	ret += indent+""
	ret += indent+""
	ret += "\n"
	indent = "\n\t"

	# TRIGGER
	# TRIGGER
	ret += indent+"# Rule " + rule.name
	ret += indent+"def " + rule.name + "_trigger(self, snode, n2id, stack=None, inCombo=False, equivalences=None, checked=True, finish=''):"
	indent += "\t"
	ret += indent+"if stack == None: stack=[]"
	ret += indent+"if equivalences == None: equivalences=[]"
	if len(optimal_node_list)>0:
		ret += indent+"if not checked:"
		indent += "\t"
		lelele = 0
		symbols_in_stack = []
		moreErrorInformation = ''
		for n in optimal_node_list:
			lelele += 1
			ret += indent+"test_symbol_"+n+" = snode.graph.nodes[n2id['"+n+"']]"
			ret += indent+"if not (test_symbol_"+n+".sType == '"+nodesPlusParameters[n].sType+"'"
			moreErrorInformation = "print 'test_symbol_"+n+".sType == "+nodesPlusParameters[n].sType+"' , test_symbol_"+n+".sType == '"+nodesPlusParameters[n].sType+"'"
			for other in symbols_in_stack:
				ret += " and test_symbol_"+n+".name!=test_symbol_" + str(other) + ".name"
			conditions, number, linksInfo = extractNewLinkConditionsFromList(rule.lhs.links, n, symbols_in_stack)
			ret += conditions
			ret += "):"
			symbols_in_stack.append(n)
			indent += "\t"
			ret += indent+moreErrorInformation
			for l in linksInfo:
				ret += indent+l
			ret += indent+"raise WrongRuleExecution('"+rule.name+"_trigger"+str(lelele)+"')"
			indent = indent[:-1]
		indent = indent[:-1]
        #ret += indent+"smap = "+COPY_OPTION+"(n2id)"
	ret += indent+"newNode = WorldStateHistory(snode)"
	ret += indent+"global lastNodeId"
	ret += indent+"lastNodeId += 1"
	ret += indent+"newNode.nodeId = lastNodeId"
	if thisIsActuallyAHierarchicalRule:
		ret += indent+"newNode.parentNodeToExplore = " + COPY_OPTION + "(snode)"
		ret += indent+"newNode.parentNodeToExploreWith = self." + rule.name + "_COMBOINSIDE"
		ret += indent+"newNode.stackP = "+COPY_OPTION+"(stack)"
		ret += indent+"newNode.equivalencesP = "+COPY_OPTION+"(equivalences)"
	# Create nodes
	newNodes, deleteNodes, retypeNodes = rule.lhs.getNodeChanges(rule.rhs, rule.parametersAST)
	ret += indent+"# Create nodes"
	for newNode in newNodes:
		ret += indent+"newName = str(getNewIdForSymbol(newNode))"
                ret += indent+"n2id['"+newNode.name+"'] = newName"
		ret += indent+"newNode.graph.nodes[newName] = AGMSymbol(newName, '"+newNode.sType+"')"
	ret += indent+"# Retype nodes"
	# Retype nodes
	for retypeNode in retypeNodes:
		ret += indent+"newNode.graph.nodes[n2id['"+retypeNode.name+"']].sType = '"+rule.rhs.nodes[retypeNode.name].sType + "'"
	ret += indent+"# Remove nodes"
	# Remove nodes
	for deleteNode in deleteNodes:
                ret += indent+"del newNode.graph.nodes[n2id['"+deleteNode.name+"']]"
	if len(deleteNodes)>0:
		ret += indent+"newNode.graph.removeDanglingEdges()"
	# Remove links
	newLinks, deleteLinks = rule.lhs.getLinkChanges(rule.rhs)
	ret += indent+"# Remove links"
	if len(deleteLinks)>0:
		deleteLinks_str = ''
		for l in range(len(deleteLinks)):
			if l > 0: deleteLinks_str += ", "
			deleteLinks_str += "[n2id['" + deleteLinks[l].a + "'], n2id['" + deleteLinks[l].b + "'], '" + deleteLinks[l].linkType + "']"
		ret += indent+"newNode.graph.links = [x for x in newNode.graph.links if [x.a, x.b, x.linkType] not in [ "+deleteLinks_str+" ]]"
	# Create links
	ret += indent+"# Create links"
	for newLink in newLinks:
                ret += indent+"l = AGMLink(n2id['"+newLink.a+"'], n2id['"+newLink.b+"'], '"+newLink.linkType+"')"
		ret += indent+"if not l in newNode.graph.links:"
		ret += indent+"\tnewNode.graph.links.append(l)"
	# Quantifier-related code (EFFECT)
	# <<<
	if rule.effectAST != None:
		ret += indent+"# Textual effects"
		ret += indent+"nodes = "+COPY_OPTION+"(newNode.graph.nodes)"
		indentP = indent
		try:
			effectCode, indent, effectId, stuff = normalRuleImplementation_EFFECT(rule.effectAST, indent)
		except:
			print 'Error in the "effects" section of rule', rule.name
			sys.exit(-1)
		ret += indentP+'backVars = n2id.keys()'
		ret += effectCode
		# These three lines remove temporal variables from the scope (defined in n2id)
		ret += indentP+'for k in n2id.keys():'
		ret += indentP+'\tif not k in backVars:'
		ret += indentP+'\t\tdel n2id[k]'

	# >>>
	# Misc stuff
	indent = '\n\t\t'
	ret += indent+"# Misc stuff"
	ret += indent+"if not inCombo:"
	ret += indent+"\tnewNode.cost += "+str(rule.cost)
	ret += indent+"\tnewNode.depth += 1"
	ret += indent+"newNode.history.append('" + rule.name + "@' + str(n2id) )"
	ret += indent+"if finish!='': newNode.history.append(finish)"
	ret += indent+"return newNode"
	ret += indent+""
	ret += indent+""
	ret += "\n"
	return ret


## Generation of the python code for rules' preconditions
#
# @ingroup AGGLGeneration
#
# @param precondition Precondition AST
# @param indent
# @param modifier
# @param stuff
#
# @retval Tuple containing:
# - code: String containing the resulting code
# - indent:
# - formulaId:
# - stuff:
def normalRuleImplementation_PRECONDITION(precondition, indent, modifier='', stuff=None):
	if stuff == None: stuff = {'availableid':0}
	if len(precondition) == 0:
		return '', indent, modifier, stuff
	# Split the list in its head and body
	preconditionType, preconditionBody = precondition[0], precondition[1:]
	formulaId = stuff['availableid']
	stuff['availableid'] += 1
	ret = ''

	if preconditionType == "not":
		preconditionBody = preconditionBody[0]
		text, indent, formulaIdRet, stuff = normalRuleImplementation_PRECONDITION(preconditionBody, indent, 'not', stuff)
		ret += text
		ret += indent+'precondition'+str(formulaId)+' = not precondition'+str(formulaIdRet)+' # this is a not'
	elif preconditionType == "or":
		ret += indent+'precondition'+str(formulaId)+' = False # or initialization'
		for part in preconditionBody[0]:
			text, indent, formulaIdRet, stuff = normalRuleImplementation_PRECONDITION(part, indent, 'or', stuff)
			ret += text
			ret += indent+'if precondition'+str(formulaIdRet)+' == True: # inside OR'
			ret += indent+'\tprecondition'+str(formulaId)+' = True # make OR true'
		ret += indent+'if precondition'+str(formulaId)+' == True: # IF OR'
	elif preconditionType == "and":
		ret += indent+'precondition'+str(formulaId)+' = True # AND initialization as true'
		first = True
		for part in preconditionBody[0]:
			if first: first = False
			else:
				ret += indent+'if precondition'+str(formulaId)+': # if still true'
				indent += '\t'
			text, indent, formulaIdRet, stuff = normalRuleImplementation_PRECONDITION(part, indent, 'and', stuff)
			ret += text
			ret += indent+'if precondition'+str(formulaIdRet)+' == False: # if what\'s inside the AND is false'
			ret += indent+'\tprecondition'+str(formulaId)+' = False # make the AND false'
	elif preconditionType == "forall":
		ret += indent+'precondition'+str(formulaId)+' = True # FORALL initialization as true'
		indentA = indent
		for V in preconditionBody[0]:
			n = V[0]
			t = V[1]
			ret += indent+"for symbol_"+n+"_name in nodes:"
			indent += "\t"
			ret += indent+"if precondition"+str(formulaId)+"==False: break"
			ret += indent+"symbol_"+n+" = nodes[symbol_"+n+"_name]"
			ret += indent+"n2id['"+n+"'] = symbol_"+n+"_name"
			ret += indent+"if symbol_"+n+".sType == '"+t+"':  # now the body of the FORALL"
			indent += "\t"
		text, indent, formulaIdRet, stuff = normalRuleImplementation_PRECONDITION(preconditionBody[1], indent, 'forall', stuff)
		ret += text
		ret += indent+'if precondition'+str(formulaIdRet)+' == False: # if what\'s inside the FORALL is false'
		ret += indent+'\tprecondition'+str(formulaId)+' = False # make the FORALL false'
		for V in preconditionBody[0]:
			ret += indentA+"del n2id['"+V[0]+"']"
		indent = indentA
	elif preconditionType == "when":
		ret += indent+'precondition'+str(formulaId)+' = True # WHEN initialization as true'
		text, indent, formulaIdRet1, stuff = normalRuleImplementation_PRECONDITION(preconditionBody[0], indent, 'whenA', stuff)
		ret += text
		ret += indent+'if precondition'+str(formulaIdRet1)+' == True: # if what\'s inside the WHEN(if) is True'
		text, indent, formulaIdRet2, stuff = normalRuleImplementation_PRECONDITION(preconditionBody[1], indent+'\t', 'whenB', stuff)
		ret += text
		ret += indent+'if precondition'+str(formulaIdRet2)+' == False: # if what\'s inside the WHEN(then) is False'
		ret += indent+'\tprecondition'+str(formulaId)+' = False # make the WHEN false'
	elif preconditionType == "=":
		ret += indent+'precondition'+str(formulaId) + ' = (n2id["'+preconditionBody[0]+'"] == n2id["'+preconditionBody[1]+'"])'
	elif preconditionType == "create":
		print '\'create\' statements are not allowed in preconditions'
		sys.exit(1)
	elif preconditionType == "delete":
		print '\'delete\' statements are not allowed in preconditions'
		sys.exit(1)
	elif preconditionType == "retype":
		print '\'retype\' statements are not allowed in preconditions'
		sys.exit(1)
	else:
		try:
			ret += indent+'precondition'+str(formulaId) + ' = ['
			ret += 'n2id["'+preconditionBody[0]+'"], '
			ret += 'n2id["'+preconditionBody[1]+'"], "'
			ret += preconditionType + '"] in snode.graph.links # LINK'
		except:
			print 'ERROR IN', preconditionType
			print 'ERROR IN', preconditionBody
			traceback.print_exc()
	return ret, indent, formulaId, stuff

## Generation of the python code for rules' effects
#
# @ingroup AGGLGeneration
#
# @param precondition Effect AST
# @param indent
# @param modifier
# @param stuff
#
# @retval Tuple containing:
# - code: string containing the resulting code
# - indent: the indentation level for the generated text (it depends on the context)
# - modifier:
# - stuff:
def normalRuleImplementation_EFFECT(effect, indent, modifier='', stuff=None):
	if stuff == None: stuff = {'availableid':0, 'mode':'normal'}
	if len(effect) == 0:
		return '', indent, modifier, stuff
	# Split the list in its head and body
	effectType, effectBody = effect[0], effect[1:]
	formulaId = stuff['availableid']
	stuff['availableid'] += 1
	ret = ''
	#print '<',effectType,'>'

	if effectType == "not":
		effectBody = effectBody[0]
		if stuff['mode'] == 'condition':
			print 'CONDITION NOT EFFECT inside not, the body is', effectBody
			text, indent, formulaIdRet, stuff = normalRuleImplementation_EFFECT(effectBody, indent, 'not', stuff)
			ret += text
			ret += indent+'if effect'+str(formulaIdRet)+' == False: # inside not'
			ret += indent+'\teffect'+str(formulaId)+'is TRUE! [because '+str(formulaIdRet)+' is False] # not'
			ret += indent+'else: # inside not is false'
			ret += indent+'\teffect'+str(formulaId)+'is FALSE! [because '+str(formulaIdRet)+' is True] # not'
		else:
			text, indent, formulaIdRet, stuff = normalRuleImplementation_EFFECT(effectBody, indent, 'not', stuff)
			ret += text
	elif effectType == "or":
		print 'OR statements are not allowed in effects'
		sys.exit(1)
	# Partially done, the conditional mode is not tested
	elif effectType == "and":
		if stuff['mode'] == "condition":
			ret += indent+'effect'+str(formulaId)+' = True # AND initialization as true'
			first = True
			for part in effectBody[0]:
				if first: first = False
				else:
					ret += indent+'if effect'+str(formulaId)+': # if still true'
					indent += '\t'
				text, indent, formulaIdRet, stuff = normalRuleImplementation_EFFECT(part, indent, 'and', stuff)
				ret += text
				ret += indent+'if effect'+str(formulaIdRet)+' == False: # if what\'s inside the AND is false'
				ret += indent+'\teffect'+str(formulaId)+' = False # make the AND false'
		else:
			for part in effectBody[0]:
				text, indent, formulaIdRet, stuff = normalRuleImplementation_EFFECT(part, indent, 'and', stuff)
				ret += text
	elif effectType == "forall":
		for V in effectBody[0]:
			n = V[0]
			t = V[1]
			ret += indent+"for symbol_"+n+"_name in nodes:"
			indent += "\t"
			ret += indent+"symbol_"+n+" = nodes[symbol_"+n+"_name]"
			ret += indent+"n2id['"+n+"'] = symbol_"+n+"_name"
			ret += indent+"if symbol_"+n+".sType == '"+t+"':  # now the body of the FORALL"
			indent += "\t"
		text, indent, formulaIdRet, stuff = normalRuleImplementation_EFFECT(effectBody[1], indent, 'forall', stuff)
		ret += text
	elif effectType == "when":
		stuff['mode'] = 'condition'
		text, indent, formulaIdRet1, stuff = normalRuleImplementation_EFFECT(effectBody[0], indent, 'whenA', stuff)
		stuff['mode'] = 'normal'
		ret += text
		ret += indent+'if condition'+str(formulaIdRet1)+' == True: # if what\'s inside the WHEN(if) is True'
		text, indent, formulaIdRet2, stuff = normalRuleImplementation_EFFECT(effectBody[1], indent+'\t', 'whenB', stuff)
		ret += text
	elif effectType == "=":
		print '\'=\' statements are not allowed in effects'
		sys.exit(1)
	elif effectType == "create":
		ret += indent+"newName = str(getNewIdForSymbol(newNode))"
		ret += indent+"smap['"+effectBody[0]+"'] = newName"
		ret += indent+"newNode.graph.nodes[newName] = AGMSymbol(newName, '"+effectBody[1]+"')"
	elif effectType == "delete":
		ret += indent+"del newNode.graph.nodes[smap['"+effectBody[0]+"']]"
		ret += indent+"newNode.graph.removeDanglingEdges()"
	elif effectType == "retype":
		ret += indent+"newNode.graph.nodes[n2id['"+effectBody[0]+"']].sType = '"+effectBody[1]+"'"
	else:
		if effectBody[0] == '':
			raise Exception('ERROR IN: '+str(effect))
		try:
			if stuff['mode'] == "condition":
				ret += indent+'condition'+str(formulaId) + ' = ['
				ret += 'n2id["'+effectBody[0]+'"],'
				ret += 'n2id["'+effectBody[1]+'"],"'
				ret += effectType + '"] in snode.graph.links # LINK'
			else:
				if modifier == 'not':
					ret += indent+'if [n2id["'+effectBody[0]+'"], n2id["'+effectBody[1]+'"], "' + effectType + '"] in newNode.graph.links:'
					#ret += indent+'\tnewNode.graph.links.remove([n2id["'+effectBody[0]+'"], n2id["'+effectBody[1]+'"], "' + effectType + '"])'
					ret += indent+'\tnewNode.graph.links = [x for x in newNode.graph.links if x.a!=n2id["'+effectBody[0]+'"] or x.b!=n2id["'+effectBody[1]+'"] or x.linkType!="'+effectType+'"]'
				else:
					ret += indent+'if not [n2id["'+effectBody[0]+'"], n2id["'+effectBody[1]+'"], "' + effectType + '"] in newNode.graph.links:'
					ret += indent+'\tnewNode.graph.links.append(AGMLink(n2id["'+effectBody[0]+'"], n2id["'+effectBody[1]+'"], "' + effectType + '"))'
		except:
			print 'ERROR IN', effectType
			print 'ERROR IN', effectBody
			traceback.print_exc()
	return ret, indent, formulaId, stuff



##  djijo ioju oij o
#
# @ingroup AGGLGeneration
#
def generate(agm, skipPassiveRules):
	text = ''
	text += constantHeader()
	text += ruleDeclaration(agm)
	text += ruleTriggerDeclaration(agm)
	for rule in agm.rules:
		text += ruleImplementation(rule)
	return text


def getOptimalTargetNodeCheckOrder(graph):
	## Generate Link list
	linkList = []
	for link_i in range(len(graph.links)):
		link = graph.links[link_i]
		linkList.append([link.a, link.b, link.linkType])
	linkList = sorted(linkList, key=itemgetter(0, 1, 2))
	## Initialize separated list for constants and variables
	consts = []
	varbls = []
	for n_n in graph.nodes:
		n = str(n_n)
		if (n[0] in "0123456789"):
			consts.append(n)
		else:
			varbls.append(n)
	initialSort = consts + varbls
	## generate points for close-to-optimal list
	counter = dict()
	for n in varbls:
		counter[n] = 0
	for n in varbls:
		for link in linkList:
			if link[0] in consts+[n] or link[1] in consts+[n]:
				counter[n] = counter[n] + 1
	## actually generate the optimal list
	optimal_node_list_t = []
	for n in counter.keys():
		optimal_node_list_t.append((counter[n], n))
	optimal_node_list_t = sorted(optimal_node_list_t, reverse=True)
	optimal_node_list = copy.deepcopy(consts)
	for o in optimal_node_list_t:
		optimal_node_list.append(o[1])
	## return!
	return optimal_node_list

## Generates target
#
# @ingroup AGGLGeneration
#
# @param The graph used to generate the target
#
# @retval The python code used to check the target world state
def generateTarget(graph):
	ret = """import copy, sys
sys.path.append('/usr/local/share/agm/')\nfrom AGGL import *\nfrom agglplanner import *

def computeMaxScore(a, b, maxScore):
	s = 0
	for i in a: s+=i
	for i in b: s+=i
	if s > maxScore: return s
	return maxScore

def CheckTarget(graph):"""
	indent = "\n\t"
	# Make a copy of the current graph node list
	ret += indent+"n2id = dict()\n"
	## Generate Link list
	linkList = []
	for link_i in range(len(graph.links)):
		link = graph.links[link_i]
		linkList.append([link.a, link.b, link.linkType])
	linkList = sorted(linkList, key=itemgetter(0, 1, 2))

	ret += indent+"maxScore = 0"
	ret += indent+"scoreEasy = 0"
	ret += '\n'
	easy = 1
	if True:
		ret += indent+"# Easy score"
		typesDict = dict()
		for n in graph.nodes:
			t = graph.nodes[n].sType
			easy += 1
			if t in typesDict:
				typesDict[t] += 1
			else:
				typesDict[t] = 1
		ret += indent+"typesDict = dict()"
		for t in typesDict:
			ret += indent+"typesDict['"+t+"'] = " + str(typesDict[t])
		ret += indent+"for n in graph.nodes:"
		ret += indent+"	if graph.nodes[n].sType in typesDict:"
		ret += indent+"		scoreEasy += 1"
		ret += indent+"		typesDict[graph.nodes[n].sType] -= 1"
		ret += indent+"		if typesDict[graph.nodes[n].sType] == 0:"
		ret += indent+"			del typesDict[graph.nodes[n].sType]"
		ret += '\n'

	conditionsListList = []
	# Generate the loop that checks the model
	symbols_in_stack = []
	score = 0

	pops = []

	ret += indent+"# Hard score"
	ret += indent+"scoreNodes = []"
	ret += indent+"scoreLinks = []"

	#for n_n in graph.nodes:
	for n_n in getOptimalTargetNodeCheckOrder(graph):
		n = str(n_n)
		ret += indent+"# "+n
		if (n[0] in "0123456789") and n in graph.nodes: # This checks the node is already in the model
			ret += indent+"symbol_"+n+"_name = '" + n + "'"
		else: # otherwise, we're talking about a variable!
			ret += indent+"for symbol_"+n+"_name in graph.nodes:"
			indent += "\t"
		ret += indent+"symbol_"+n+" = graph.nodes[symbol_"+n+"_name]"
		ret += indent+"n2id['"+n+"'] = symbol_"+n+"_name"
		ret += indent+"linksVal = 0"
		for cond in newLinkScore(graph.links, n_n, symbols_in_stack):
			ret += indent+cond
		ret += indent+"scoreLinks.append(linksVal)"
		pops.append(indent+'scoreLinks.pop()')
		ret += indent+"maxScore = computeMaxScore(scoreNodes, scoreLinks, maxScore)"
		ret += indent+"if symbol_"+n+".sType == '"+graph.nodes[n_n].sType+"'"
		for other in symbols_in_stack:
			ret += " and symbol_"+n+".name!=symbol_" + str(other) + ".name"
		conditions, number, ll = extractNewLinkConditionsFromList(graph.links, n_n, symbols_in_stack)
		conditions = conditions.replace("snode.graph", "graph")
		conditionsListList.append( [conditions, number] )
		ret += conditions
		ret += ":"
		symbols_in_stack.append(n_n)
		indent += "\t"
		score += scorePerContition
		ret += indent + "scoreNodes.append(100)"
		pops.append(indent+'scoreNodes.pop()')
		ret += indent + "maxScore = computeMaxScore(scoreNodes, scoreLinks, maxScore)"

	allConditionsStr = ''
	for c in conditionsListList:
		allConditionsStr += c[0]
	conditionsSeparated = allConditionsStr.split("and ")
	realCond = 0
	for cond in conditionsSeparated:
		if len(cond) > 1:
			realCond += 1
			#ret += indent+"if " + cond + ": scoreNodes += "+str(scorePerContition)+""
	ret += indent+"if maxScore == " + str(score + realCond*scorePerContition) + ": return maxScore+scoreEasy, True"


	# Rule ending
	while len(pops)>0:
		ret += pops.pop()
	indent = "\n\t"
	ret += indent+"return maxScore+scoreEasy, False"
	ret += "\n"
	return ret
