import math, traceback, itertools, copy, sys

from pddlAGGL import *

def distance(x1, y1, x2, y2):
	return math.sqrt(math.pow(x1-x2, 2) + math.pow(y1-y2, 2))

class AGMSymbol(object):
	def __init__(self, name, sType, pos=[0,0]):
		object.__init__(self)
		self.name = name
		self.sType = sType
		self.pos = pos
		self.color = 'white'
		self.attributes = dict()
	def __str__(self):
		return self.toString()
	def __repr__(self):
		return self.toString()
	def toString(self):
		return str(self.name)+':'+str(self.sType)
	@property
	def x(self):
		return self.pos[0]
	@property
	def y(self):
		return self.pos[1]
	def linkedTo(self, node, graph):
		for link in graph.links:
			if link.a == self.name and link.b == node.name:
				return True
		return False


class AGMLink(object):
	def __init__(self, a, b, linkType, enabled=True):
		object.__init__(self)
		self.a = a
		self.b = b
		self.linkType = linkType
		self.color = 'white'
		self.enabled = enabled
	def toString(self):
		v = ''
		if self.enabled:
			return '\t\t'+str(self.a)+'->'+str(self.b)+'('+v+str(self.linkType)+')'
		else:
			return '\t\t'+str(self.a)+'->'+str(self.b)+'('+v+str(self.linkType)+')*'
	def __cmp__(self, other):
		this =  self.linkType+" "+ self.a+" "+ self.b+" "+str( self.enabled)
		if isinstance(other, list):
			nhis = other[2]+" "+other[0]+" "+other[1]+" "
			if len(other)>3:
				nhis+=str(other[3])
			else:
				nhis+=str(True)
		else:
			nhis = other.linkType+" "+other.a+" "+other.b+" "+str(other.enabled)
		if this < nhis: return -1
		if this > nhis: return +1
		return 0
	def __eq__(self, other):
		#this = self.linkType+" "+ self.a+" "+ self.b+" "+str( self.enabled)
		if isinstance(other, list):
			if other[2] != self.linkType: return False
			if other[0] != self.a: return False
			if other[1] != self.b: return False
			if len(other)>3:
				if str(self.enabled) != str(other[3]): return False
			else:
				if str(self.enabled) != str(True): return False
		else:
			if self.a != other.a: return False
			if self.b != other.b: return False
			if self.linkType != other.linkType: return False
			if self.enabled != other.enabled: return False
		return True
	def __ne__(self, other):
		this =  self.linkType+" "+ self.a+" "+ self.b+" "+str( self.enabled)
		if isinstance(other, list):
			nhis = other[2]+" "+other[0]+" "+other[1]+" "
			if len(other)>3:
				nhis+=str(other[3])
			else:
				nhis+=str(True)
		else:
			nhis = other.linkType+" "+other.a+" "+other.b+" "+str(other.enabled)
		if this == nhis:
			return False
		return True
	def __hash__(self):
		return len(self.a+self.b+self.linkType+str(self.enabled))
	def __str__(self):
		ret = '('+self.a+')--['+self.linkType+']--('+self.b+') '
		if not self.enabled:
			ret += '*'
		return ret
	def __repr__(self):
		return self.__str__()

class AGMGraph(object):
	def __init__(self, nodes=None, links=None, side='n'):
		object.__init__(self)
		if links == None:
			links = list()
		if nodes == None:
			nodes = dict()
		self.nodes = nodes
		self.links = links
		self.side = side
	def removeDanglingEdges(self):
		linkindex = 0
		while linkindex < len(self.links):
			e = self.links[linkindex]
			try:
				v1 = self.nodes[e.a]
				v2 = self.nodes[e.b]
				linkindex += 1
			except:
				del self.links[linkindex]
	def __str__(self):
		ret = 'NODES [ '
		for i in self.nodes:
			ret += ' '+str(self.nodes[i])+' '
		ret += ']\n'
		ret += 'LINKS [ '
		for l in self.links:
			ret += ' '+str(l)+' '
		ret += ']\n'
		return ret
	def __repr__(self):
		return self.__str__()
	def __cmp__(self):
		#print '__cmp__'
		return object.__cmp__(self)
	def __hash__(self):
		#print '__hash__'
		return (len(self.nodes), len(self.links))
	def __eq__(self, other):
		try:
			# Basic: number of nodes
			if len(self.nodes) != len(other.nodes):
				return False
			# Basic: number of links
			if len(self.links) != len(other.links):
				return False
			# Exhaustive nodes
			for l in self.nodes:
				if not l in other.nodes:
					return False
			#for l in other.nodes:                       SINCE WE HAVE THE SAME NUMBER OF NODES (checked above) ITS
				#if not l in self.nodes:                  NOT NECESSARY TO PERFORM THE CHECK IN BOTH WAYS
					#return False
			# Exhaustive links
			for l in range(len(self.links)):
				if not self.links[l] in other.links:
					return False
			#for l in range(len(other.links)):           SINCE WE HAVE THE SAME NUMBER OF LINKS (checked above) ITS
				#if not other.links[l] in self.links:     NOT NECESSARY TO PERFORM THE CHECK IN BOTH WAYS
					#return False
			return True
		except:
			return False

	def __cmp__(self, other):
		# Basic: number of nodes
		if len(self.nodes) != len(other.nodes):
			return False
		# Basic: number of links
		if len(self.links) != len(other.links):
			return False

		return True
	def getName(self, xa, ya, diameter):
		minDist = -1
		minName = None
		for name in self.nodes.keys():
			dist = distance(xa, ya, self.nodes[name].pos[0], self.nodes[name].pos[1])
			if dist < diameter/2:
				if dist < minDist or minDist < 0:
					minDist = dist
					minName = name
		if minDist > -1:
			return minName, True
		else:
			raise Exception("")
	def setColors(self, other, left):
		for name in self.nodes.keys():
			if not name in other.nodes.keys():
				if left:
					self.nodes[name].color = "red"
				else:
					self.nodes[name].color = "green"
			else:
				if self.nodes[name].sType != other.nodes[name].sType:
					self.nodes[name].color = "gray"
				else:
					self.nodes[name].color = "white"
		for l in range(len(self.links)):
			if not self.links[l] in other.links:
				if left:
					self.links[l].color = "red"
				else:
					self.links[l].color = "green"
			else:
				self.links[l].color = "white"
	def getNodeChanges(self, other, parameters):
		# Generate temporal variables
		parametersDict = dict()
		for i in parameters:
			parametersDict[i[0]] = AGMSymbol(i[0], i[1])
		L = dict( self.nodes, **parametersDict)
		R = dict(other.nodes, **parametersDict)
		# Initialize return values
		toCreate = []
		toRemove = []
		toRetype = []
		# Find symbols to create and retype
		for name in L.keys():
			if not name in R.keys():
					toRemove.append(L[name])
			else:
				if L[name].sType != R[name].sType:
					toRetype.append(L[name])
		# Find symbols to remove
		for name in R.keys():
			if not name in L.keys():
					toCreate.append(R[name])
		return toCreate, toRemove, toRetype
	def getLinkChanges(self, other):
		toCreate = []
		toRemove = []
		for l in range(len(self.links)):
			if not self.links[l] in other.links:
				toRemove.append(self.links[l])
		for l in range(len(other.links)):
			if not other.links[l] in self.links:
				toCreate.append(other.links[l])
		return toCreate, toRemove
	def getNameRelaxed(self, xa, ya, diameter):
		minDist = -1
		minName = None
		for name in self.nodes.keys():
			dist = distance(xa, ya, self.nodes[name].pos[0], self.nodes[name].pos[1])
			if dist < minDist or minDist < 0:
				minDist = dist
				minName = name
		if minDist > -1:
			return minName, True
		else:
			return '', False
	def getCenter(self, xa, ya, diameter):
		name, found = self.getName(xa, ya, diameter)
		if found:
			return self.nodes[name].pos[0], self.nodes[name].pos[1]
		else:
			raise BasicException("")


	def addNode(self, x, y, name, stype):
		if not name in self.nodes.keys():
			self.nodes[name] = AGMSymbol(name, stype, [x,y])
	def removeNode(self, x, y, diameter):
		name, found = self.getName(x, y, diameter)
		if found:
			del self.nodes[name]
		else:
			pass
	def moveNode(self, name, x, y, diameter):
		if name in self.nodes:
			self.nodes[name].pos = [x, y]
		elif name == '':
			pass
		else:
			print 'No such node', str(name)+'. Internal editor error.'
			pass
	def addEdge(self, a, b, linkname='link'):
		self.links.append(AGMLink(a, b, linkname, True))
	def removeEdge(self, a, b):
		i = 0
		while i < len(self.links):
			l = self.links[i]
			if l.a == a and l.b == b:
				del self.links[i]
			else:
				i += 1
	def toString(self):
		ret = '\t{\n'
		for v in self.nodes.keys():
			ret += '\t\t' +str(self.nodes[v].name) + ':'+self.nodes[v].sType + '(' + str(int(self.nodes[v].pos[0])) + ','+ str(int(self.nodes[v].pos[1])) + ')\n'
		for l in self.links:
			ret += l.toString() + '\n'
		return ret+'\t}'

	def nodeTypes(self):
		ret = set()
		for k in self.nodes.keys():
			ret.add(self.nodes[k].sType)
		return ret

	def nodeNames(self):
		ret = set()
		for k in self.nodes.keys():
			ret.add(self.nodes[k].name)
		return ret

	def linkTypes(self):
		ret = set()
		for l in self.links:
			ret.add(l.linkType)
		return ret
	
	def getNode(self, identifier):
		return self.nodes[identifier]

	def toXML(self, path):
		f = open(path, 'w')
		f.write('<AGMModel>\n')
		for n in self.nodes:
			f.write('\t<symbol id="'+str(self.nodes[n].name)+'" type="'+str(self.nodes[n].sType)+'">\n')
			for attr in self.nodes[n].attributes.keys():
				f.write('\t\t<attribute key="'+attr+'" value="'+self.nodes[n].attributes[attr]+'" />\n')
			f.write('\t</symbol>\n')
		for l in self.links:
			f.write('\t<link src="'+str(l.a)+'" dst="'+str(l.b)+'" label="'+str(l.linkType)+'" />\n')
		f.write('</AGMModel>\n\n')
		f.close()

class AGMRule(object):
	def __init__(self, name='', lhs=None, rhs=None, passive=False, cost=1, parameters=[], precondition=None, effect=None):
		object.__init__(self)
		self.name = name
		self.lhs = lhs
		self.rhs = rhs
		self.cost = cost
		self.passive = passive
		self.mindepth = 0
		self.parameters = parameters
		if self.parameters == None: self.parameters = []
		self.precondition = precondition
		self.effect = effect
		if lhs == None:
			self.lhs = AGMGraph()
		if rhs == None:
			self.rhs = AGMGraph()
	def toString(self):
		passiveStr = "active"
		if self.passive: passiveStr = "passive"
		costStr = str(self.cost)
		ret = self.name + ' : ' + passiveStr + '(' + costStr + ')'
		if self.mindepth != 0:
			ret += 'mindepth(' + str(self.mindepth) + ')'
		ret += '\n{\n'
		ret += self.lhs.toString() + '\n'
		ret += '\t=>\n'
		ret += self.rhs.toString() + '\n'
		if len(self.parameters) > 0:
			ret += '\tparameters\n\t{' + self.parameters + '}\n'
		if len(self.precondition) > 0:
			ret += '\tprecondition\n\t{' + self.precondition + '}\n'
		if len(self.effect) > 0:
			ret += '\teffect\n\t{' + self.effect + '}\n'
		ret += '}'
		return ret
	def forgetNodesList(self):
		return list(set(self.lhs.nodes).difference(set(self.rhs.nodes)))
	def newNodesList(self):
		return list(set(self.rhs.nodes).difference(set(self.lhs.nodes)))
	def stayingNodeSet(self):
		return set(self.lhs.nodeNames()).intersection(set(self.rhs.nodeNames()))
	def stayingNodeList(self):
		return list(self.stayingNodeSet())
	def anyNewOrForgotten(self):
		if len(self.newNodesList())==0:
			if len(self.newNodesList())==0:
				return False
		return True
	def nodeTypes(self):
		return self.lhs.nodeTypes().union(self.rhs.nodeTypes())
	def nodeNames(self):
		return self.lhs.nodeNames().union(self.rhs.nodeNames())
	def linkTypes(self):
		return self.lhs.linkTypes().union(self.rhs.linkTypes())

class AGMComboRule(object):
	def __init__(self, name='', passive=False, cost=1, ats=list(), eqs=list()):
		object.__init__(self)
		self.name = name
		self.passive = passive
		self.atoms = ats
		self.cost = cost
		self.equivalences = []
		for eq in eqs:
			#print eq
			eqResult = list()
			for element in eq:
				eqResult.append([element[0], element[1]])
			self.equivalences.append(eqResult)
	def toString(self):
		#print self.equivalences
		passiveStr = "active"
		if self.passive: passiveStr = "passive"
		ret = self.name + ' : ' + passiveStr + '('+ str(self.cost) +')\n{\n'
		for a in self.atoms:
			ret += '\t' + a[0] + ' as ' + a[1] + '\n'
		ret += '\twhere:\n'
		for e in self.equivalences:
			first = True
			for element in e:
				if first:
					first = False
					ret += '\t'  + element[0] + '.' + element[1]
				else:
					ret += ' = ' + element[0] + '.' + element[1]
			ret += '\n'
		ret += '}\n'
		return ret


class AGM(object):
	def __init__(self):
		object.__init__(self)
		self.rules = []
	def addRule(self, rule):
		self.rules.append(rule)


class AGMFileData(object):
	def __init__(self):
		object.__init__(self)
		self.properties = dict()
		self.agm = AGM()

	def addRule(self, rule):
		self.agm.addRule(rule)

	def toFile(self, filename):
		writeString = ''
		for k,v in self.properties.items():
			writeString += str(k) + '=' + str(v) + '\n'
		writeString += '===\n'
		# Rules
		for r in self.agm.rules:
			writeString = writeString + r.toString() + '\n\n'
		w = open(filename, 'w')
		w.write(writeString)
		w.close()

	def generatePDDL(self, filename, skipPassiveRules=False):
		#print 'Generating (partial =', str(skipPassiveRules)+') PDDL file'
		w = open(filename, 'w')
		a = copy.deepcopy(self.agm)
		text = AGMPDDL.toPDDL(a, self.properties["name"], skipPassiveRules)
		w.write(text)
		w.close()
		
	def generateAGGLPlannerCode(self, filename, skipPassiveRules=False):
		w = open(filename, 'w')
		a = copy.deepcopy(self.agm)
		import generateAGGLPlannerCode
		text = generateAGGLPlannerCode.generate(a, skipPassiveRules)
		w.write(text)
		w.close()
		
