from pyparsing import Word, alphas, alphanums, nums, OneOrMore, Optional, Suppress, ZeroOrMore, Group, StringEnd
import math
import traceback
import itertools

from pddlAGGL import *
from agmbdAGGL import *


def distance(x1, y1, x2, y2):
	return math.sqrt(math.pow(x1-x2, 2) + math.pow(y1-y2, 2))

class AGMSymbol(object):
	def __init__(self, name, sType, pos):
		object.__init__(self)
		self.name = name
		self.sType = sType
		self.pos = pos
	def toString(self):
		return str(self.name)+':'+str(self.sType)+'('+str(self.pos[0])+','+str(self.pos[1])+')'

class AGMLink(object):
	def __init__(self, a, b, linkType, enabled):
		object.__init__(self)
		self.a = a
		self.b = b
		self.linkType = linkType
		self.enabled = enabled
	def toString(self):
		v = ''
		if not self.enabled: v = 'q '
		return '\t\t'+str(self.a)+'->'+str(self.b)+'('+v+str(self.linkType)+')'
	def __cmp__(self, other):
		this =  self.linkType+ self.a+ self.b
		nhis = other.linkType+other.a+other.b
		if this < nhis: return -1
		if this > nhis: return +1
		return 0
	def __eq__(self, other):
		this =  self.linkType+ self.a+ self.b
		nhis = other.linkType+other.a+other.b
		if this == nhis:
			return True
		return False
	def __ne__(self, other):
		this =  self.linkType+ self.a+ self.b
		nhis = other.linkType+other.a+other.b
		if this == nhis:
			return False
		return True
	def __hash__(self):
		return len(self.a+self.b+self.linkType)
	def __str__(self):
		return self.a+'-->'+self.b+' ('+self.linkType+')'
	def __repr__(self):
		return self.a+'-->'+self.b+' ('+self.linkType+')'

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
			return '', False
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
			return -1, -1


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
		name, found = self.getNameRelaxed(x, y, diameter)
		if found:
			self.nodes[name].pos = [x, y]
		else:
			pass
	def addEdge(self, a, b):
		self.links.append(AGMLink(a, b, 'link', True))
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
			ret += '\t\t' +str(self.nodes[v].name) + ':'+self.nodes[v].sType + '(' + str(self.nodes[v].pos[0]) + ','+ str(self.nodes[v].pos[1]) + ')\n'
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

class AGMRule(object):
	def __init__(self, name='', config=None, lhs=None, rhs=None):
		object.__init__(self)
		self.name = name
		self.lhs = lhs
		self.rhs = rhs
		self.configuration = config
		if lhs == None:
			self.lhs = AGMGraph()
		if rhs == None:
			self.rhs = AGMGraph()
	def toString(self):
		if type(self.configuration) == type(AGMConfiguration('')):
			ret = self.name + ' : ' + self.configuration.toString() + '\n{\n'
		else:
			ret = self.name + ' : #\n{\n'
		ret += self.lhs.toString() + '\n'
		ret += '\t=>\n'
		ret += self.rhs.toString() + '\n'
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

class AGMAgent(object):
	def __init__(self, name):
		self.name = name
		self.states = dict()
		self.statesList = []
	def addState(self, statename):
		if type(statename) == type(''):
			self.states[statename] = AGMAgentState(statename, self.name)
		else:
			self.states[statename] = statename
		if not statename in self.statesList:
			self.statesList.append(statename)
	def addUnnamedState(self):
		initialName = self.name + 'State'
		possibleNumber = len(self.states)
		name = initialName + str(possibleNumber)
		while name in self.states.keys():
			possibleNumber = possibleNumber + 1
			name = initialName + str(possibleNumber)
		self.addState(AGMAgentState(name,self.name))
		return name
	def validStateNames(self):
		r = []
		for x in self.states:
			r.append(self.states[x].name)
		return r
	def toString(self):
		s = self.name + ' ('
		for n in self.statesList:
			s += ' ' + n.name
		s += ' )'
		return s

class AGMConfiguration(object):
	def __init__(self, name):
		self.name = name
	def toString(self):
		return self.name

class AGMAgentState(object):
	def __init__(self, name, parentName):
		self.name = name
		self.parentName = parentName

class AGM(object):
	def __init__(self):
		object.__init__(self)
		self.rules = []
		self.agents = dict()
		self.configurations = dict()
		self.agentList = []
		self.configurationList = []
	def addRule(self, rule):
		self.rules.append(rule)
	def addConfiguration(self, conf):
		if type(conf) != type(AGMConfiguration('')):
			raise BaseException
		if not conf.name in self.configurationList:
			self.configurationList.append(conf.name)
		self.configurations[conf.name] = conf
	def addAgent(self, agent):
		if not agent in self.agentList: self.agentList.append(agent)
		a = AGMAgent(agent)
		self.agents[agent] = a
	def addUnnamedAgent(self):
		initialName = 'agent'
		possibleNumber = len(self.agents)
		name = initialName + str(possibleNumber)
		while name in self.agents.keys():
			possibleNumber = possibleNumber + 1
			name = initialName + str(possibleNumber)
		self.addAgent(name)
		return name
	def addUnnamedConfiguration(self):
		initialName = 'configuration'
		possibleNumber = len(self.configurations)
		name = initialName + str(possibleNumber)
		while name in self.configurations.keys():
			possibleNumber = possibleNumber + 1
			name = initialName + str(possibleNumber)
		c = AGMConfiguration(name)
		self.addConfiguration(c)
		return c
	def addUnnamedAgentState(self, agent):
		return self.agents[agent].addUnnamedState()
	def addAgentState(self, agent, statename):
		return self.agents[agent].addState(statename)
	def getConfigRule(self, rule):
		if type(rule) == type(AGMRule('s')):
			rule = rule.name
		ret = None
		for r in self.rules:
			if r.name == rule:
				ret = r.configuration
				break
		return ret
	def setConfigRule(self, rule, conf):
		if type(conf) != type(AGMConfiguration('')):
			conf = AGMConfiguration(conf)
		found = False
		for r in self.rules:
			if r.name == rule:
				r.configuration = conf
				found = True
		if found == False:
			raise BaseException


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
		# Agents
		writeString += 'agents\n'
		writeString += '{\n'
		for r in self.agm.agentList:
			writeString = writeString + self.agm.agents[r].toString() + '\n'
		writeString += '}\n'
		# Configs
		writeString += 'configurations'
		writeString += '{ '
		for r in self.agm.configurationList:
			writeString = writeString + r + ' '
		writeString += '}\n'
		# Table
		writeString += self.tableString
		writeString += '===\n'
		for r in self.agm.rules:
			writeString = writeString + r.toString() + '\n\n'
		w = open(filename, 'w')
		w.write(writeString)
		w.close()

	def generatePDDL(self, filename):
		w = open(filename, 'w')
		w.write(AGMPDDL.toPDDL(self.agm, self.properties["name"]))
		w.close()
		
	def generateAGMBehaviorDescription(self, filename):
		w = open(filename, 'w')
		w.write(AGMBD.toAGMBehaviorDescription(self.agm, self.properties["name"]))
		w.close()
				
