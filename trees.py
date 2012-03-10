# -----------------------------------------------------------------------------------------------------------------
# proof-of-concept dynamic object oriented tree generator 
# for terasology project
# written by cynthia kurtz
# -----------------------------------------------------------------------------------------------------------------

import os, sys, random, math
import numpy as np

from trees_graphics import *
from trees_world import *

# -------------------------------------------------------------------------------------------
# TO DO
# -------------------------------------------------------------------------------------------

# DONE set up sequenced output dirs
# DONE make branches have non-perpendicular angles
# DONE make non-woody stems photosynthesize, a little
# DONE improve photosynthesis - use sun array
# DONE draw sun array on graph
# DONE add apical dominance
# DONE make absolute limit on how many internodes can be created - to prevent params blowing up
# DONE use s curve for photosynthesis
# DONE??? put random number on seed unique to tree
# FIXED problem: gaps
# DONE add internode width
# DONE add leafCluster petiole and leafCluster shape
# DONE add leafCluster angle with stem
# DONE put in root growth
# DONE do water and nutrient uptake - water and nutrient grids, like sun grid
# DONE add seeking behavior for internodes (stem and root)

# put in flower and fruit clusters

# add limits on parameters (in comments)
# do several parameter sets
# make code more clear with many comments
# write comment on board
# upload to git repository?

# NOT DOING think about collision avoidance and growth around occupied blocks

# -------------------------------------------------------------------------------------------
class TreePart():
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, location, forward, side, biomass=0, water=0, minerals=0):
		self.tree = tree
		self.parent = parent
		self.age = 0
		self.alive = True
		
		self.biomass = biomass
		self.water = water
		self.minerals = minerals
		
		self.forward = forward
		self.side = side
		self.location = location
		self.blocks = []
		
	def nextDay(self):
		self.releaseAllUsedBlocks()
		self.nextDay_Uptake()
		self.nextDay_Consumption()
		self.nextDay_Distribution()
		self.nextDay_Growth()
		self.nextDay_Drawing()
		self.nextDay_SignalPropagation()
		self.age += 1
		
	def die(self):
		self.alive = False
	
	def releaseAllUsedBlocks(self):
		for location in self.blocks:
			releaseLocation(location, self)
		self.blocks = []
		
	def claimStartBlock(self):
		self.blocks = [self.location]
		claimLocation(self.location, self)
		
	def claimSeriesOfBlocks(self, locations):
		for location in locations:
			if not location in self.blocks:
				self.blocks.append(location)
				claimLocation(location, self)
				
# -------------------------------------------------------------------------------------------
class Meristem(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, root, numberOnInternode, location, forward, side, apical=False, biomass=0, water=0, minerals=0):
		TreePart.__init__(self, tree, parent, location, forward, side, 
						biomass=START_MERISTEM_BIOMASS[root], water=START_MERISTEM_WATER[root], minerals=START_MERISTEM_MINERALS[root])
		self.apical = apical
		self.root = root
		self.numberOnInternode = numberOnInternode
		self.active = False
		
		self.reproductive = False
		if self.tree.reproductivePhaseHasStarted:
			self.reproduce()
		
	def buildInternode(self, firstOnTree=False):
		if self.apical:
			newSide = rotateAround(self.forward, self.side, 1)
			if self.parent:
				parentBranchForward = self.parent.parentBranchForward
			else:
				if self.root:
					parentBranchForward = "down"
				else:
					parentBranchForward = "up"
		else:   
			if self.parent:
				newSide = self.side
				parentBranchForward = self.parent.forward
			else:
				if self.root:
					parentBranchForward = "down"
					newSide = self.tree.firstRootInternodeSideDirection
				else:
					parentBranchForward = "up"
					newSide = self.tree.firstInternodeSideDirection
		firstOnBranch = firstOnTree or not self.apical
		
		newInternode = Internode(self.tree, self.parent, self.root, self.location, self.forward, newSide, 
								firstOnTree=firstOnTree, firstOnBranch=firstOnBranch, parentBranchForward=parentBranchForward,
								iAmABranchOffMyParent=not self.apical)
		if self.parent:
			if self.apical:
				self.parent.addChildInternode(newInternode)
			else:
				self.parent.addBranchInternode(newInternode)
		return newInternode
	
	def buildFlowerCluster(self):
		if self.apical:
			newSide = rotateAround(self.forward, self.side, 1)
		else:   
			if self.parent:
				newSide = self.side
			else:
				newSide = self.tree.firstInternodeSideDirection
		newFlowerCluster = FlowerCluster(self.tree, self.parent, self.numberOnInternode, self.apical, self.location, self.forward, newSide)
		if self.parent:
			self.parent.addFlowerCluster(newFlowerCluster)
		
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		if self.alive:
			if self.biomass - BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root] < MERISTEM_DIES_IF_BIOMASS_GOES_BELOW[self.root] or \
				self.water - WATER_USED_BY_MERISTEM_PER_DAY[self.root] < MERISTEM_DIES_IF_WATER_GOES_BELOW[self.root] or \
				self.minerals - MINERALS_USED_BY_MERISTEM_PER_DAY[self.root] < MERISTEM_DIES_IF_MINERALS_GOES_BELOW[self.root]:
				self.die()
				#print 'meristem died', self.biomass, self.water, self.minerals, self.root
			else:
				if self.apical:
					self.active = True
				else:
					self.calculateActivityLevel()
				if self.active:
					self.biomass -= BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root]
					self.water -= WATER_USED_BY_MERISTEM_PER_DAY[self.root]
					self.minerals -= MINERALS_USED_BY_MERISTEM_PER_DAY[self.root]
				
	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		if self.alive:
			if self.active:
				if self.reproductive:
					if self.biomass >= BIOMASS_TO_MAKE_ONE_FLOWER_CLUSTER and \
						self.water >= WATER_TO_MAKE_ONE_FLOWER_CLUSTER and \
						self.minerals >= MINERALS_TO_MAKE_ONE_FLOWER_CLUSTER:
						self.buildFlowerCluster()
						self.parent.removeMeristemThatMadeInternode(self)
				else:
					if self.biomass >= BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root] and \
						self.water >= WATER_TO_MAKE_ONE_PHYTOMER[self.root] and \
						self.minerals >= MINERALS_TO_MAKE_ONE_PHYTOMER[self.root]:
						self.buildInternode()
						self.parent.removeMeristemThatMadeInternode(self)
						
	def nextDay_Drawing(self):
		if self.apical:
			location = self.parent.locationForApicalMeristem()
		else:
			location, forward, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
		self.location = location
		if DRAW_MERISTEMS:
			self.claimStartBlock()
		
	def calculateActivityLevel(self):
		if self.alive and not self.active:
			if self.tree.numInternodesCreated <= MAX_NUM_INTERNODES_ON_TREE_EVER[self.root]:
				distance = self.distanceOfParentFromBranchApex()
				if distance > 0:
					probability = BRANCHING_PROBABILITY[self.root] * distance / APICAL_DOMINANCE_EXTENDS_FOR[self.root]
					probability = max(0.0, min(1.0, probability))
					randomNumber = random.random() 
					self.active = randomNumber < probability
					if self.active and not self.root and self.tree.reproductivePhaseHasStarted:
						self.reproduce()
					#print 'axillary meristem distance', distance, 'prob', probability, 'number', randomNumber, 'active', self.active
		
	def distanceOfParentFromBranchApex(self):
		distance = 0
		internode = self.parent
		while internode:
			distance += 1
			internode = internode.child
		if internode and not internode.apicalMeristem: # apical meristem is missing, perhaps removed
			distance = APICAL_DOMINANCE_EXTENDS_FOR[self.root] + 1 # you can develop if the apex was removed
		return distance
		
	def nextDay_SignalPropagation(self):
		pass
	
	def acceptBiomass(self, biomassOffered):
		if self.alive and self.active:
			biomassINeed = max(0, (BIOMASS_TO_MAKE_ONE_PHYTOMER[self.root] + BIOMASS_USED_BY_MERISTEM_PER_DAY[self.root]) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
	
	def acceptWater(self, waterOffered):
		if self.alive and self.active:
			waterINeed = max(0, (WATER_TO_MAKE_ONE_PHYTOMER[self.root] + WATER_USED_BY_MERISTEM_PER_DAY[self.root]) - self.water)
		else:
			waterINeed = 0
		waterIWillAccept = min(waterOffered, waterINeed)
		self.water += waterIWillAccept
		return waterIWillAccept
	
	def acceptMinerals(self, mineralsOffered):
		if self.alive and self.active:
			mineralsINeed = max(0, (MINERALS_TO_MAKE_ONE_PHYTOMER[self.root] + MINERALS_USED_BY_MERISTEM_PER_DAY[self.root]) - self.minerals)
		else:
			mineralsINeed = 0
		mineralsIWillAccept = min(mineralsOffered, mineralsINeed)
		self.minerals += mineralsIWillAccept
		return mineralsIWillAccept
	
	def reproduce(self):
		print 'in meristem reproduce', self.alive, self.root
		if self.alive and not self.root:
			if self.apical:
				probabilityIWillTurnReproductive = PROBABILITY_THAT_ANY_APICAL_MERISTEM_WILL_SWITCH_TO_REPRO_MODE
			else:
				probabilityIWillTurnReproductive = PROBABILITY_THAT_ANY_AXILLARY_MERISTEM_WILL_SWITCH_TO_REPRO_MODE
			randomNumber = random.random()
			print probabilityIWillTurnReproductive, randomNumber
			if randomNumber < probabilityIWillTurnReproductive:
				self.reproductive = True
	
	def describe(self, outputFile, indentCounter=0):
		if self.root:
			rootOrNot = ' root '
		else:
			rootOrNot = ''
		if self.apical:
			apicalOrAxillary = ' apical '
		else:
			apicalOrAxillary = ' axillary '
		outputFile.write(INDENT * indentCounter + rootOrNot + apicalOrAxillary + ' meristem: ' + ' alive ' + str(self.alive) + \
			' biomass ' + str(self.biomass) + " water " + str(self.water) + " minerals " + str(self.minerals) + \
			" location " + str(self.location) + " active " + str(self.active) + " reproductive " + str(self.reproductive) +
			" forward " + self.forward + " side " + self.side)
		outputFile.write("\n")
		
# -------------------------------------------------------------------------------------------
class Internode(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, root, location, forward, side, firstOnTree, firstOnBranch, parentBranchForward, iAmABranchOffMyParent):
		TreePart.__init__(self, tree, parent, location, forward, side, 
						biomass=START_INTERNODE_BIOMASS[root], water=START_INTERNODE_WATER[root], minerals=START_INTERNODE_MINERALS[root])
		self.child = None
		self.branches = []
		self.flowerClusters = []
		self.fruitClusters = []
		
		self.root = root
		self.firstOnTree = firstOnTree
		self.firstOnBranch = firstOnBranch
		self.parentBranchForward = parentBranchForward
		self.iAmABranchOffMyParent = iAmABranchOffMyParent
		
		self.tree.numInternodesCreated += 1
		self.randomSway = random.randrange(RANDOM_INTERNODE_SWAY[self.root]) - RANDOM_INTERNODE_SWAY[self.root] // 2
		
		self.woody = (INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS[self.root] == 0)
		if self.firstOnTree:
			self.length = FIRST_INTERNODE_LENGTH_AT_CREATION[self.root]
		else:
			self.length = INTERNODE_LENGTH_AT_CREATION[self.root]
		self.width = INTERNODE_WIDTH_AT_CREATION[self.root]
		self.endLocation = self.location
		
		if not self.root:
			self.buildLeafClusters()
		self.buildMeristems()
		
	def buildMeristems(self):
		location = self.locationForApicalMeristem()
		self.apicalMeristem = Meristem(self.tree, self, self.root, 0, location, self.forward, self.side, apical=True)
		self.axillaryMeristems = []
		for i in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			location, forward, side = self.locationAndDirectionsForAxillaryMeristem(i)
			newAxillaryMeristem = Meristem(self.tree, self, self.root, i, location, forward, side, apical=False)
			self.axillaryMeristems.append(newAxillaryMeristem)
		
	def buildLeafClusters(self):
		self.leafClusters = []
		for i in range(AXILLARY_MERISTEMS_PER_INTERNODE[self.root]):
			location, forward, side = self.locationAndDirectionsForLeafCluster(i)
			newLeafCluster = LeafCluster(self.tree, self, i, location, forward, side)
			self.leafClusters.append(newLeafCluster)
			
	def locationForApicalMeristem(self):
		aboveGround = not self.root
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1, aboveGround)
		return locationOneFurther
	
	def locationAndDirectionsForAxillaryMeristem(self, meristemNumber):
		aboveGround = not self.root
		if AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 1:
			meristemForward = self.side
		elif AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 2:
			if meristemNumber == 1:
				meristemForward = self.side
			else:
				meristemForward = rotateAround(self.forward, self.side, 2)
		else:
			if meristemNumber == 1:
				meristemForward = self.side
			else:
				meristemForward = rotateAround(self.forward, self.side, meristemNumber)
		location = displacementInDirection(self.endLocation, meristemForward, self.width//2, aboveGround)
		meristemSide = self.forward
		return location, meristemForward, meristemSide
		
	def locationAndDirectionsForLeafCluster(self, leafClusterNumber):
		locationOneDownFromEnd = displacementInDirection(self.endLocation, self.forward, -1)
		if AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 1:
			leafClusterForward = self.side
		elif AXILLARY_MERISTEMS_PER_INTERNODE[self.root] == 2:
			if leafClusterNumber == 1:
				leafClusterForward = self.side
			else:
				leafClusterForward = rotateAround(self.forward, self.side, 2)
		else:
			if leafClusterNumber == 1:
				leafClusterForward = self.side
			else:
				leafClusterForward = rotateAround(self.forward, self.side, leafClusterNumber)
		location = displacementInDirection(locationOneDownFromEnd, leafClusterForward, self.width//2)
		leafClusterSide = self.forward
		# looks strange if leafClusters don't point to the side
		# cfk keep this?
		if leafClusterSide in ["up", "down"]:
			leafClusterSide = rotateAround(leafClusterForward, leafClusterSide, 1)
		return location, leafClusterForward, leafClusterSide
	
	def locationForChildInternode(self):
		aboveGround = not self.root
		locationOneFurther = displacementInDirection(self.endLocation, self.forward, 1, aboveGround)
		return locationOneFurther
		
	def addChildInternode(self, internode):
		self.child = internode
		
	def addBranchInternode(self, internode):
		self.branches.append(internode)
		
	def addFlowerCluster(self, flowerCluster):
		self.flowerClusters.append(flowerCluster)
				
	def addFruitCluster(self, fruitCluster):
		self.fruitClusters.append(fruitCluster)
				
	def acceptBiomass(self, biomassOffered):
		# the internode, because it is a piping system, takes biomass it doesn't need so it can pass it on
		self.biomass += biomassOffered
		return biomassOffered
	
	def acceptWater(self, waterOffered):
		self.water += waterOffered
		return waterOffered
	
	def acceptMinerals(self, mineralsOffered):
		self.minerals += mineralsOffered
		return mineralsOffered
	
	def removeMeristemThatMadeInternode(self, meristem):
		if meristem.apical:
			self.apicalMeristem = None
		else:
			self.axillaryMeristems.remove(meristem)
			
	def removeFlowerClusterThatMadeFruitCluster(self, flowerCluster):
		self.flowerClusters.remove(flowerCluster)
		
	def nextDay_Uptake(self):
		if self.alive:
			if (not self.root) and (not self.woody):
				sunProportion = sun[(self.endLocation[0], self.endLocation[1])]
				numBlocksShadingMe = blocksOccupiedAboveLocation(self.endLocation, self)
				if numBlocksShadingMe > 0:
					shadeProportion = max(0.0, min(1.0, 1.0 - 1.0 * numBlocksShadingMe / SHADE_TOLERANCE))
				else:
					shadeProportion = 1.0
				waterProportion = self.water / OPTIMAL_INTERNODE_WATER[self.root]
				mineralsProportion = self.minerals / OPTIMAL_INTERNODE_MINERALS[self.root]
				biomassProportion = self.biomass / OPTIMAL_INTERNODE_BIOMASS[self.root]
				combinedEffectsProportion = sunProportion * 0.2 + shadeProportion + 0.2 + waterProportion + 0.2 + mineralsProportion * 0.2 + biomassProportion * 0.2
				combinedEffectsProportion = max(0.0, min(1.0, combinedEffectsProportion))
				sCurve = 1.0 - math.exp(-0.65 * combinedEffectsProportion)
				self.newBiomass =  sCurve * OPTIMAL_INTERNODE_PHOTOSYNTHATE
				self.biomass += self.newBiomass
			if self.root:
				availableWater, locationsConsidered = waterOrMineralsInRegion("water", self.endLocation, ROOT_WATER_EXTRACTION_RADIUS)
				if availableWater > 0:
					for location in locationsConsidered:
						if water.has_key(location):
							waterAtLocation = water[location]
						else:
							waterAtLocation = 0
						if waterAtLocation > 0:
							waterExtractedFromLocation = ROOT_WATER_EXTRACTION_EFFICIENCY * waterAtLocation
							self.water += waterExtractedFromLocation
							water[location] -= waterExtractedFromLocation
				availableMinerals, locationsConsidered = waterOrMineralsInRegion("minerals", self.endLocation, ROOT_MINERAL_EXTRACTION_RADIUS)
				if availableMinerals > 0:
					for location in locationsConsidered:
						if minerals.has_key(location):
							mineralsAtLocation = minerals[location]
							if mineralsAtLocation > 0:
								mineralsExtractedFromLocation = ROOT_MINERAL_EXTRACTION_EFFICIENCY * mineralsAtLocation
								self.minerals += mineralsExtractedFromLocation
								minerals[location] -= mineralsExtractedFromLocation
	
	def nextDay_Consumption(self):
		if self.alive:
			if self.woody:
				biomassINeedToUseToday = 0
				waterINeedToUseToday = 0
				mineralsINeedToUseToday = 0
			else:
				biomassINeedToUseToday = BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root]
				waterINeedToUseToday = WATER_USED_BY_INTERNODE_PER_DAY[self.root]
				mineralsINeedToUseToday = MINERALS_USED_BY_INTERNODE_PER_DAY[self.root]
			if self.biomass - biomassINeedToUseToday < INTERNODE_DIES_IF_BIOMASS_GOES_BELOW[self.root] or \
					self.water - waterINeedToUseToday < INTERNODE_DIES_IF_WATER_GOES_BELOW[self.root] or \
					self.minerals - mineralsINeedToUseToday < INTERNODE_DIES_IF_MINERALS_GOES_BELOW[self.root]:
				self.die()
				#print 'internode died', self.biomass, self.water, self.minerals, self.root
			else:
				self.biomass -= biomassINeedToUseToday
				self.water -= waterINeedToUseToday
				self.minerals -= mineralsINeedToUseToday
	
	def die(self):
		sendDieSignalTo = []
		if not self.root:
			sendDieSignalTo.extend(self.leafClusters)
		sendDieSignalTo.extend([self.apicalMeristem])
		sendDieSignalTo.extend(self.axillaryMeristems)
		sendDieSignalTo.extend([self.child])
		sendDieSignalTo.extend(self.branches)
		for sendTo in sendDieSignalTo:
			if sendTo:
				sendTo.die()
	
	def nextDay_Distribution(self):
		# internode can still act as piping system even if it is dead
		parts = self.gatherDistributees(BIOMASS_DISTRIBUTION_ORDER[self.root])
		for part in parts:
			if part:
				extra = max(0, self.biomass - OPTIMAL_INTERNODE_BIOMASS[self.root] - BIOMASS_USED_BY_INTERNODE_PER_DAY[self.root])
				if extra > 0:
					toBeGivenAway = extra * BIOMASS_DISTRIBUTION_SPREAD_PERCENT[self.root] / 100.0
					taken = part.acceptBiomass(toBeGivenAway)
					self.biomass -= taken
		parts = self.gatherDistributees(WATER_DISTRIBUTION_ORDER[self.root])
		for part in parts:
			if part:
				extra = max(0, self.water - OPTIMAL_INTERNODE_WATER[self.root] - WATER_USED_BY_INTERNODE_PER_DAY[self.root])
				if extra > 0:
					toBeGivenAway = extra * WATER_DISTRIBUTION_SPREAD_PERCENT[self.root] / 100.0
					taken = part.acceptWater(toBeGivenAway)
					self.water -= taken
		parts = self.gatherDistributees(MINERALS_DISTRIBUTION_ORDER[self.root])
		for part in parts:
			if part:
				extra = max(0, self.minerals - OPTIMAL_INTERNODE_MINERALS[self.root] - MINERALS_USED_BY_INTERNODE_PER_DAY[self.root])
				if extra > 0:
					toBeGivenAway = extra * MINERALS_DISTRIBUTION_SPREAD_PERCENT[self.root] / 100.0
					taken = part.acceptMinerals(toBeGivenAway)
					self.minerals -= taken
				
	def gatherDistributees(self, order):
		distributees = []
		for name in order:
			if name == "leaf clusters":
				if not self.root:
					distributees.extend(self.leafClusters)
			elif name == "flower clusters":
				if not self.root:
					distributees.extend(self.flowerClusters)
			elif name == "fruit clusters":
				if not self.root:
					distributees.extend(self.fruitClusters)
			elif name == "apical meristems":
				distributees.extend([self.apicalMeristem])
			elif name == "axillary meristems":
				distributees.extend(self.axillaryMeristems)
			elif name == "child":
				distributees.extend([self.child])
			elif name == "branches":
				distributees.extend(self.branches)
			elif name == "parent":
				distributees.extend([self.parent])
			elif name == "root":
				if (not self.root) and self.firstOnTree:
					distributees.extend([self.tree.firstRootInternode])
			elif name == "above-ground tree":
				if self.root and self.firstOnTree:
					distributees.extend([self.tree.firstInternode])
		return distributees
				
	def nextDay_Growth(self):
		self.woody = self.age > INTERNODES_TURN_WOODY_AFTER_THIS_MANY_DAYS
		if self.alive:
			biomassBasedProportion = self.biomass / OPTIMAL_INTERNODE_BIOMASS[self.root]
			waterBasedProportion = self.water / OPTIMAL_INTERNODE_WATER[self.root]
			mineralsBasedProportion  = self.minerals / OPTIMAL_INTERNODE_MINERALS[self.root]
			overallProportion = biomassBasedProportion * waterBasedProportion * mineralsBasedProportion
			if self.firstOnTree:
				self.length = int(round(overallProportion * FIRST_INTERNODE_LENGTH_AT_FULL_SIZE[self.root]))
				self.length = max(FIRST_INTERNODE_LENGTH_AT_CREATION[self.root], min(FIRST_INTERNODE_LENGTH_AT_FULL_SIZE[self.root], self.length))
			else:
				self.length = int(round(overallProportion * INTERNODE_LENGTH_AT_FULL_SIZE[self.root]))
				self.length = max(INTERNODE_LENGTH_AT_CREATION[self.root], min(INTERNODE_LENGTH_AT_FULL_SIZE[self.root], self.length))
			self.width = int(round(overallProportion * INTERNODE_WIDTH_AT_FULL_SIZE[self.root]))
			self.width = max(INTERNODE_WIDTH_AT_CREATION[self.root], min(INTERNODE_WIDTH_AT_FULL_SIZE[self.root], self.width))
		
	def nextDay_Drawing(self):
		aboveGround = not self.root
		if not self.iAmABranchOffMyParent:
			if self.parent:
				self.location = self.parent.locationForChildInternode()
		# testing the parent branch forward is a kludgy way of trying to find out if you have branched
		# off the main trunk without saving the information
		# NOT USING - CFK FIX
		angleInDegrees = ANGLE_BETWEEN_STEM_AND_BRANCH_NOT_OFF_TRUNK[self.root]
		self.endLocation = endPointOfAngledLine(self.location, self.length, 
					angleInDegrees, self.randomSway, self.forward, self.parentBranchForward, self.side, aboveGround)
		if not self.woody and INTERNODES_SEEK_RADIUS[self.root] > 0:
			self.endLocation = seekBetterLocation(self.endLocation, self.root, INTERNODES_SEEK_RADIUS[self.root])
		if (self.root and DRAW_ROOTS) or (not self.root and DRAW_STEMS):
			locationsBetween = locationsBetweenTwoPoints(self.location, self.endLocation, self.length)
			self.claimStartBlock()
			self.claimSeriesOfBlocks(locationsBetween)
			if self.width > 1:
				for location in locationsBetween:
					circleLocations = circleAroundPoint(location, self.width, self.forward, self.side, aboveGround)
					self.claimSeriesOfBlocks(circleLocations)
			
	def nextDay_SignalPropagation(self):
		sendSignalTo = []
		if not self.root:
			sendSignalTo.extend(self.leafClusters)
			sendSignalTo.extend(self.flowerClusters)
			sendSignalTo.extend(self.fruitClusters)
		sendSignalTo.extend([self.apicalMeristem])
		sendSignalTo.extend(self.axillaryMeristems)
		sendSignalTo.extend([self.child])
		sendSignalTo.extend(self.branches)
		for sendTo in sendSignalTo:
			if sendTo:
				sendTo.nextDay()
		
	def reproduce(self):
		if not self.root:
			print 'internode is sending on repro signal'
			sendSignalTo = []
			sendSignalTo.extend([self.apicalMeristem])
			sendSignalTo.extend(self.axillaryMeristems)
			sendSignalTo.extend([self.child])
			sendSignalTo.extend(self.branches)
			for sendTo in sendSignalTo:
				if sendTo:
					sendTo.reproduce()
		
	def describe(self, outputFile, indentCounter=0):
		if self.root:
			rootOrNot = "root"
		else:
			rootOrNot = ""
		outputFile.write(INDENT * indentCounter + rootOrNot + ' internode: ' + ' alive ' + str(self.alive) + \
			' biomass ' + str(self.biomass) + " water " + str(self.water) + " minerals " + str(self.minerals) + \
			" location " + str(self.location) + " forward " + self.forward + " side " + self.side)
		outputFile.write("\n")
		if not self.root:
			for leafCluster in self.leafClusters:
				leafCluster.describe(outputFile, indentCounter+1)
		if self.apicalMeristem:
			self.apicalMeristem.describe(outputFile, indentCounter+1)
		for meristem in self.axillaryMeristems:
			if meristem:
				meristem.describe(outputFile, indentCounter+1)
		if self.child:
			self.child.describe(outputFile, indentCounter+1)
			
# -------------------------------------------------------------------------------------------
class LeafCluster(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, numberOnInternode, location, forward, side):
		TreePart.__init__(self, tree, parent, location, forward, side, 
						biomass=START_LEAF_CLUSTER_BIOMASS, water=START_LEAF_CLUSTER_WATER, minerals=START_LEAF_CLUSTER_MINERALS)
		self.numberOnInternode = numberOnInternode
		self.length = LEAF_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_LEAF_CLUSTER_SWAY) - RANDOM_LEAF_CLUSTER_SWAY // 2
		self.newBiomass = 0
				
	def nextDay_Uptake(self):
		if self.alive:
			sunProportion = sun[(self.location[0], self.location[1])]
			numBlocksShadingMe = blocksOccupiedAboveLocation(self.location, self)
			if numBlocksShadingMe > 0:
				shadeProportion = max(0.0, min(1.0, 1.0 - 1.0 * numBlocksShadingMe / SHADE_TOLERANCE))
			else:
				shadeProportion = 1.0
			waterProportion = self.water / OPTIMAL_LEAF_CLUSTER_WATER
			mineralsProportion = self.minerals / OPTIMAL_LEAF_CLUSTER_MINERALS
			biomassProportion = self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
			#combinedEffectsProportion = sunProportion * shadeProportion * waterProportion * mineralsProportion * biomassProportion
			combinedEffectsProportion = sunProportion * 0.2 + shadeProportion + 0.2 + waterProportion + 0.2 + mineralsProportion * 0.2 + biomassProportion * 0.2
			combinedEffectsProportion = max(0.0, min(1.0, combinedEffectsProportion))
			sCurve = 1.0 - math.exp(-0.65 * combinedEffectsProportion)
			self.newBiomass =  sCurve * OPTIMAL_LEAF_PHOTOSYNTHATE
			#print sunProportion, numBlocksShadingMe, shadeProportion, waterProportion, mineralsProportion, biomassProportion
			#print '.....', combinedEffectsProportion, sCurve, self.newBiomass
			#self.newBiomass =  max(0.0, combinedEffectsProportion * (1.0 - math.exp(-0.65 * OPTIMAL_LEAF_PHOTOSYNTHATE)))
			self.biomass += self.newBiomass
		else:
			self.newBiomass = 0
	
	def nextDay_Consumption(self):
		if self.alive:
			if self.biomass - BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY < LEAF_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW or \
					self.water - WATER_USED_BY_LEAF_CLUSTER_PER_DAY < LEAF_CLUSTER_DIES_IF_WATER_GOES_BELOW or \
					self.minerals - MINERALS_USED_BY_LEAF_CLUSTER_PER_DAY < LEAF_CLUSTER_DIES_IF_MINERALS_GOES_BELOW:
				self.die()
			else:
				self.biomass -= BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY
				self.water -= WATER_USED_BY_LEAF_CLUSTER_PER_DAY
				self.minerals -= MINERALS_USED_BY_LEAF_CLUSTER_PER_DAY

	def nextDay_Distribution(self):
		if self.alive:
			extraBiomass = max(0, self.biomass - OPTIMAL_LEAF_CLUSTER_BIOMASS)
			biomassTakenByParent = self.parent.acceptBiomass(extraBiomass)
			self.biomass -= biomassTakenByParent
	
	def nextDay_Growth(self):
		location, direction, side = self.parent.locationAndDirectionsForLeafCluster(self.numberOnInternode)
		self.location = location
		if self.alive:
			biomassBasedProportion = self.biomass / OPTIMAL_LEAF_CLUSTER_BIOMASS
			waterBasedProportion = self.water / OPTIMAL_LEAF_CLUSTER_WATER
			mineralsBasedProportion  = self.minerals / OPTIMAL_LEAF_CLUSTER_MINERALS
			overallProportion = biomassBasedProportion * waterBasedProportion * mineralsBasedProportion
			self.length = int(round(overallProportion * LEAF_CLUSTER_LENGTH_AT_FULL_SIZE))
			self.length = max(LEAF_CLUSTER_LENGTH_AT_CREATION, min(LEAF_CLUSTER_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_Drawing(self):
		if DRAW_LEAF_CLUSTERS:
			if self.length > 1:
				spineEndLocation = endPointOfAngledLine(self.location, self.length, 
							LEAF_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward, self.side)
				spine = locationsBetweenTwoPoints(self.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / LEAF_CLUSTER_LENGTH_AT_FULL_SIZE
				# spine, pattern, angle, sides, sizeProportion, forward, side
				wings = locationsForShapeAroundSpine(spine, LEAF_CLUSTER_SHAPE_PATTERN, LEAF_CLUSTER_SHAPE_ANGLE, LEAF_CLUSTER_SIDES, 
							sizeProportion, self.forward, self.side)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_LEAF_CLUSTER_BIOMASS + BIOMASS_USED_BY_LEAF_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
	def acceptWater(self, waterOffered):
		if self.alive:
			waterINeed = max(0, (OPTIMAL_LEAF_CLUSTER_WATER + WATER_USED_BY_LEAF_CLUSTER_PER_DAY) - self.water)
		else:
			waterINeed = 0
		waterIWillAccept = min(waterOffered, waterINeed)
		self.water += waterIWillAccept
		return waterIWillAccept
	
	def acceptMinerals(self, mineralsOffered):
		if self.alive:
			mineralsINeed = max(0, (OPTIMAL_LEAF_CLUSTER_MINERALS + MINERALS_USED_BY_LEAF_CLUSTER_PER_DAY) - self.minerals)
		else:
			mineralsINeed = 0
		mineralsIWillAccept = min(mineralsOffered, mineralsINeed)
		self.minerals += mineralsIWillAccept
		return mineralsIWillAccept
	
	def describe(self, outputFile, indentCounter=0):
		outputFile.write(INDENT * indentCounter + ' leaf cluster: ' + ' alive ' + str(self.alive) + \
			' biomass ' + str(self.biomass) + ' new ' + str(self.newBiomass) + " water " + str(self.water) + " minerals " + str(self.minerals) + \
			" location " + str(self.location) + " forward " + self.forward + " side " + self.side)
		outputFile.write('\n')
		
# -------------------------------------------------------------------------------------------
class FlowerCluster(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, numberOnInternode, apical, location, forward, side):
		TreePart.__init__(self, tree, parent, location, forward, side, 
						biomass=START_FLOWER_CLUSTER_BIOMASS, water=START_FLOWER_CLUSTER_WATER, minerals=START_FLOWER_CLUSTER_MINERALS)
		self.numberOnInternode = numberOnInternode
		self.apical = apical
		self.length = FLOWER_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_FLOWER_CLUSTER_SWAY) - RANDOM_FLOWER_CLUSTER_SWAY // 2
		
	def buildFruit(self):
		newFruitCluster = FruitCluster(self.tree, self.parent, self.numberOnInternode, self.location, self.forward, self.side)
		self.parent.removeFlowerClusterThatMadeFruitCluster(self)
		self.parent.addFruitCluster(newFruitCluster)
				
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY < FLOWER_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW or \
				self.water - WATER_USED_BY_FLOWER_CLUSTER_PER_DAY < FLOWER_CLUSTER_DIES_IF_WATER_GOES_BELOW or \
				self.minerals - MINERALS_USED_BY_FLOWER_CLUSTER_PER_DAY < FLOWER_CLUSTER_DIES_IF_MINERALS_GOES_BELOW:
			self.die()
			#print 'leaf died', self.biomass, self.water, self.minerals
		else:
			self.biomass -= BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY
			self.water -= WATER_USED_BY_FLOWER_CLUSTER_PER_DAY
			self.minerals -= MINERALS_USED_BY_FLOWER_CLUSTER_PER_DAY

	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		if self.biomass >= OPTIMAL_FLOWER_CLUSTER_BIOMASS:
			self.buildFruit()
		else:
			location, direction, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
			self.location = location
			biomassBasedProportion = self.biomass / OPTIMAL_FLOWER_CLUSTER_BIOMASS
			waterBasedProportion = self.water / OPTIMAL_FLOWER_CLUSTER_WATER
			mineralsBasedProportion  = self.minerals / OPTIMAL_FLOWER_CLUSTER_MINERALS
			overallProportion = biomassBasedProportion * waterBasedProportion * mineralsBasedProportion
			self.length = int(round(overallProportion * FLOWER_CLUSTER_LENGTH_AT_FULL_SIZE))
			self.length = max(FLOWER_CLUSTER_LENGTH_AT_CREATION, min(FLOWER_CLUSTER_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_Drawing(self):
		if DRAW_FLOWER_CLUSTERS:
			if self.length > 1:
				spineEndLocation = endPointOfAngledLine(self.location, self.length, 
							FLOWER_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward, self.side)
				spine = locationsBetweenTwoPoints(self.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / FLOWER_CLUSTER_LENGTH_AT_FULL_SIZE
				# # spine, pattern, angle, sides, sizeProportion, forward, side
				wings = locationsForShapeAroundSpine(spine, FLOWER_CLUSTER_SHAPE_PATTERN, FLOWER_CLUSTER_SHAPE_ANGLE, FLOWER_CLUSTER_SIDES, 
							sizeProportion, self.forward, self.side)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_FLOWER_CLUSTER_BIOMASS + BIOMASS_USED_BY_FLOWER_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed = 0
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
	def acceptWater(self, waterOffered):
		if self.alive:
			waterINeed = max(0, (OPTIMAL_FLOWER_CLUSTER_WATER + WATER_USED_BY_FLOWER_CLUSTER_PER_DAY) - self.water)
		else:
			waterINeed = 0
		waterIWillAccept = min(waterOffered, waterINeed)
		self.water += waterIWillAccept
		return waterIWillAccept
	
	def acceptMinerals(self, mineralsOffered):
		if self.alive:
			mineralsINeed = max(0, (OPTIMAL_FLOWER_CLUSTER_MINERALS + MINERALS_USED_BY_FLOWER_CLUSTER_PER_DAY) - self.minerals)
		else:
			mineralsINeed = 0
		mineralsIWillAccept = min(mineralsOffered, mineralsINeed)
		self.minerals += mineralsIWillAccept
		return mineralsIWillAccept
	
	def describe(self, outputFile, indentCounter=0):
		outputFile.write(INDENT * indentCounter + ' flower cluster: ' + ' alive ' + str(self.alive) + \
			' biomass ' + str(self.biomass) + " water " + str(self.water) + " minerals " + str(self.minerals) + \
			" location " + str(self.location) + " forward " + self.forward + " side " + self.side)
		outputFile.write('\n')
		
# -------------------------------------------------------------------------------------------
class FruitCluster(TreePart):
# -------------------------------------------------------------------------------------------
	def __init__(self, tree, parent, numberOnInternode, location, forward, side):
		TreePart.__init__(self, tree, parent, location, forward, side, 
						biomass=START_FRUIT_CLUSTER_BIOMASS, water=START_FRUIT_CLUSTER_WATER, minerals=START_FRUIT_CLUSTER_MINERALS)
		self.numberOnInternode = numberOnInternode
		self.length = FRUIT_CLUSTER_LENGTH_AT_CREATION
		self.randomSway = random.randrange(RANDOM_FRUIT_CLUSTER_SWAY) - RANDOM_FRUIT_CLUSTER_SWAY // 2
		
	def nextDay_Uptake(self):
		pass
	
	def nextDay_Consumption(self):
		if self.biomass - BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY < FRUIT_CLUSTER_DIES_IF_BIOMASS_GOES_BELOW or \
				self.water - WATER_USED_BY_FRUIT_CLUSTER_PER_DAY < FRUIT_CLUSTER_DIES_IF_WATER_GOES_BELOW or \
				self.minerals - MINERALS_USED_BY_FRUIT_CLUSTER_PER_DAY < FRUIT_CLUSTER_DIES_IF_MINERALS_GOES_BELOW:
			self.die()
		else:
			self.biomass -= BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY
			self.water -= WATER_USED_BY_FRUIT_CLUSTER_PER_DAY
			self.minerals -= MINERALS_USED_BY_FRUIT_CLUSTER_PER_DAY

	def nextDay_Distribution(self):
		pass
	
	def nextDay_Growth(self):
		location, direction, side = self.parent.locationAndDirectionsForAxillaryMeristem(self.numberOnInternode)
		self.location = location
		biomassBasedProportion = self.biomass / OPTIMAL_FRUIT_CLUSTER_BIOMASS
		waterBasedProportion = self.water / OPTIMAL_FRUIT_CLUSTER_WATER
		mineralsBasedProportion  = self.minerals / OPTIMAL_FRUIT_CLUSTER_MINERALS
		overallProportion = biomassBasedProportion * waterBasedProportion * mineralsBasedProportion
		self.length = int(round(overallProportion * FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE))
		self.length = max(FRUIT_CLUSTER_LENGTH_AT_CREATION, min(FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE, self.length))
		
	def nextDay_Drawing(self):
		if DRAW_FRUIT_CLUSTERS:
			if self.length > 1:
				spineEndLocation = endPointOfAngledLine(self.location, self.length, 
							FRUIT_CLUSTER_ANGLE_WITH_STEM, self.randomSway, self.forward, self.parent.forward, self.side)
				spine = locationsBetweenTwoPoints(self.location, spineEndLocation, self.length)
				sizeProportion = 1.0 * self.length / FRUIT_CLUSTER_LENGTH_AT_FULL_SIZE
				# # spine, pattern, angle, sides, sizeProportion, forward, side
				wings = locationsForShapeAroundSpine(spine, FRUIT_CLUSTER_SHAPE_PATTERN, FRUIT_CLUSTER_SHAPE_ANGLE, FRUIT_CLUSTER_SIDES, 
							sizeProportion, self.forward, self.side)
				self.claimStartBlock()
				self.claimSeriesOfBlocks(spine)
				self.claimSeriesOfBlocks(wings)
			else:
				self.claimStartBlock()

	def nextDay_SignalPropagation(self):
		pass

	def acceptBiomass(self, biomassOffered):
		if self.alive:
			biomassINeed = max(0, (OPTIMAL_FRUIT_CLUSTER_BIOMASS + BIOMASS_USED_BY_FRUIT_CLUSTER_PER_DAY) - self.biomass)
		else:
			biomassINeed
		biomassIWillAccept = min(biomassOffered, biomassINeed)
		self.biomass += biomassIWillAccept
		return biomassIWillAccept
		
	def acceptWater(self, waterOffered):
		if self.alive:
			waterINeed = max(0, (OPTIMAL_FRUIT_CLUSTER_WATER + WATER_USED_BY_FRUIT_CLUSTER_PER_DAY) - self.water)
		else:
			waterINeed = 0
		waterIWillAccept = min(waterOffered, waterINeed)
		self.water += waterIWillAccept
		return waterIWillAccept
	
	def acceptMinerals(self, mineralsOffered):
		if self.alive:
			mineralsINeed = max(0, (OPTIMAL_FRUIT_CLUSTER_MINERALS + MINERALS_USED_BY_FRUIT_CLUSTER_PER_DAY) - self.minerals)
		else:
			mineralsINeed = 0
		mineralsIWillAccept = min(mineralsOffered, mineralsINeed)
		self.minerals += mineralsIWillAccept
		return mineralsIWillAccept
	
	def describe(self, outputFile, indentCounter=0):
		outputFile.write(INDENT * indentCounter + ' Fruit cluster: ' + ' alive ' + str(self.alive) + \
			' biomass ' + str(self.biomass) + " water " + str(self.water) + " minerals " + str(self.minerals) + \
			" location " + str(self.location) + " forward " + self.forward + " side " + self.side)
		outputFile.write('\n')
		
# -------------------------------------------------------------------------------------------
class Tree():
# -------------------------------------------------------------------------------------------
	def __init__(self, x, y, z):
		self.age = 0
		self.location = (x, y, z)
		self.numInternodesCreated = 0
		self.numRootInternodesCreated = 0
		self.reproductivePhaseHasStarted = False
		
		self.seed = random.random()
		random.seed(self.seed)
		self.firstInternodeSideDirection = DIRECTIONS[random.randrange(4)] # only choose from NESW, not up or down - first 4 in list
		self.firstRootInternodeSideDirection = DIRECTIONS[random.randrange(4)]
		
		firstMeristem = Meristem(self, None, False, 0, self.location, "up", self.firstInternodeSideDirection, apical=True)
		self.firstInternode = firstMeristem.buildInternode(firstOnTree=True)
		
		firstRootMeristem = Meristem(self, None, True, 0, self.location, "down", self.firstRootInternodeSideDirection, apical=True)
		self.firstRootInternode = firstRootMeristem.buildInternode(firstOnTree=True)
		
	def nextDay(self):
		if self.age == REPRODUCTIVE_MODE_STARTS_ON_DAY:
			self.reproductivePhaseHasStarted = True
			print 'tree is sending first repro signal'
			self.firstInternode.reproduce()
		self.firstInternode.nextDay()
		self.firstRootInternode.nextDay()
		self.age += 1
		
	def describe(self, outputFile):
		outputFile.write("tree\n")
		self.firstInternode.describe(outputFile)
		self.firstRootInternode.describe(outputFile)
		
def growTree(outputFolder):
	
	drawGraphs = False
	if drawGraphs:
		print 'writing distribution graphs...'
		drawSunDistribution(outputFolder)
		if PATCHY_WATER:
			drawWaterDistribution(outputFolder)
		if PATCHY_MINERALS:
			drawMineralsDistribution(outputFolder)
			
	describeTrees = True
	if describeTrees:
		outputFileName = outputFolder + 'Tree growth recording.txt'
		outputFile = open(outputFileName, 'w')
		
	try:
		
		numTrees = 1
		print 'starting simulated growth with %s tree(s)...' % numTrees
		daysPerPulse = 2
		numPulses = 15
		trees = []
		for i in range(numTrees):
			if numTrees == 1:
				xLocation = 50
				yLocation = 50
			else:
				xLocation = 10 + random.randrange(80)
				yLocation = 10 + random.randrange(80)
			zLocation = GROUND_LEVEL+1
			newTree = Tree(xLocation, yLocation, zLocation)
			trees.append(newTree)
		if describeTrees:
			outputFile.write("day zero\n")
			for tree in trees:
				tree.describe(outputFile)
		
		day = 1
		for i in range(numPulses):
			for j in range(daysPerPulse):
				if describeTrees:
					outputFile.write("day %s\n" % day)
				for tree in trees:
					tree.nextDay()
					if describeTrees:
						tree.describe(outputFile)
			drawSpace(day, outputFolder, drawTrees=True)#, drawSun=True, drawWater=True, drawMinerals=True, drawSurface=True)
			day += daysPerPulse
	
	finally:
		if describeTrees:
			outputFile.close()

	print 'done'
	
def main():
	iterations = 1
	for i in range(iterations):
		outputFolder = setUpOutputFolder("/Users/cfkurtz/Documents/personal/terasology/generated images/")
		print 'writing files to:', outputFolder
		growTree(outputFolder)
	
if __name__ == "__main__":
	main()
	
