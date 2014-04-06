#include "graphModelViewer.h"


#include <osgGA/TrackballManipulator>

SymbolNode::SymbolNode(std::string _id, std::string _stype) : osg::Group()
{
	id = _id;
	stype = _stype;
	vel = osg::Vec3(0,0,0);
	pos = osg::Vec3(0,0,0);

	billboard = new osg::Billboard();
	addChild(billboard);
	billboard->setMode(osg::Billboard::POINT_ROT_EYE);

	osg::StateSet* stateset = new osg::StateSet();
	osg::Image* image = osgDB::readImageFile("texture.png");
	if (image)
	{
		osg::Texture2D* texture = new osg::Texture2D;
		texture->setImage(image);
		texture->setFilter(osg::Texture::MIN_FILTER, osg::Texture::LINEAR);
		stateset->setTextureAttributeAndModes(0, texture, osg::StateAttribute::ON);
	}

	stateset->setMode(GL_LIGHTING, osg::StateAttribute::ON);
	setStateSet(stateset);

	osg::TessellationHints* hints = new osg::TessellationHints;
	hints->setDetailRatio(0.6f);

	sphere = new osg::ShapeDrawable(new osg::Sphere(osg::Vec3(0.0f,0.0f,0.0f), RADIUS), hints);
	billboard->addDrawable(sphere);

	osgText::Font *font = osgText::readFontFile("fonts/arial.ttf");
	osg::Vec4 fontSizeColor(0.6f, 0.0f, 0.0f, 100.0f);
	osg::Vec3 cursor;

	cursor = osg::Vec3(0, -RADIUS, 0.52*RADIUS);
	textId = new osgText::Text;
	textId->setFont(font);
	textId->setCharacterSize(120);
	textId->setAxisAlignment(osgText::TextBase::XZ_PLANE);
	textId->setPosition(cursor);
	textId->setColor(fontSizeColor);
	textId->setAlignment(osgText::Text::CENTER_CENTER);
	textId->setFontResolution(1000, 1000);
	textId->setText(id);
	billboard->addDrawable(textId);

	cursor = osg::Vec3(0, -RADIUS, -0.35*RADIUS);
	textType = new osgText::Text;
	textType->setFont(font);
	textType->setCharacterSize(120);
	textType->setAxisAlignment(osgText::TextBase::XZ_PLANE);
	textType->setPosition(cursor);
	textType->setColor(fontSizeColor);
	textType->setAlignment(osgText::Text::CENTER_CENTER);
	textType->setFontResolution(10,10);
	textType->setText(stype);
	billboard->addDrawable(textType);
}

void SymbolNode::setId(std::string str)
{
	textId->setText(str);
}

void SymbolNode::setType(std::string str)
{
	textType->setText(str);
}

void SymbolNode::setPosition(osg::Vec3 np)
{
	pos = np;
	billboard->setPosition(0, pos);
	billboard->setPosition(1, pos);
	billboard->setPosition(2, pos);
}


GraphModelEdge::GraphModelEdge(std::string _src, std::string _dst, std::string _label, std::map<std::string, SymbolNode *> *_nodeMapId) : osg::Group()
{
	src   = _src;
	dst   = _dst;
	label = _label;
	geode = new osg::Geode;
	addChild(geode);
	nodeMapId = _nodeMapId;
	SymbolNode *s1 = (*nodeMapId)[src];
	osg::Vec3 p1 = s1->pos;
	SymbolNode *s2 = (*nodeMapId)[dst];
	osg::Vec3 p2 = s2->pos;
	osg::StateSet* stateset = new osg::StateSet();
	stateset->setMode(GL_LIGHTING, osg::StateAttribute::ON);
	setStateSet(stateset);
	osg::Vec3 pInc = p2-p1;
	osg::Vec3 pIncNorm = pInc;
	pIncNorm.normalize();
	p1 = p1 + pIncNorm*RADIUS;
	p2 = p2 - pIncNorm*RADIUS;
	pInc = p2 - p1;
	float length = pInc.length();
	osg::Vec3 ii = p2-p1;
	ii.normalize();
	osg::Quat quat = quaternionFromInitFinalVector(osg::Vec3(0, 0, 1), ii);
	if (length <= 0.000001)
	{
		printf("hiuhwhuhhuwfqw\n");
		exit(1);
	}
	float effectiveLength = length-TIPSIZE;
	osg::Vec3 position(((p1+p2)/2.f)-(pIncNorm*TIPSIZE));
	line = new osg::Cylinder(position, RADIUS*0.2, effectiveLength);
	line->setRotation(quat);
	lineDrawable = new osg::ShapeDrawable(line);
	lineDrawable->setColor(osg::Vec4(0.7, 0.7, 0.7, 1));
	geode->addDrawable(lineDrawable);
	tip = new osg::Cone(p2-pIncNorm*(TIPSIZE+4), 2.*RADIUS/3., 3 *TIPSIZE);
	tip->setRotation(quat);
	tipDrawable = new osg::ShapeDrawable(tip);
	lineDrawable->setColor(osg::Vec4(0.7, 0.7, 0.7, 1));
	geode->addDrawable(tipDrawable);


	billboard = new osg::Billboard();
	addChild(billboard);
	billboard->setMode(osg::Billboard::POINT_ROT_EYE);
	osg::Vec3 cursor = osg::Vec3(0, -RADIUS, 0.52*RADIUS);
	labelText = new osgText::Text;
	osgText::Font *font = osgText::readFontFile("fonts/arial.ttf");
	osg::Vec4 fontSizeColor(0.2f, 0.0f, 0.0f, 100.0f);
	labelText->setFont(font);
	labelText->setCharacterSize(120);
	labelText->setAxisAlignment(osgText::TextBase::XZ_PLANE);
	labelText->setPosition(cursor);
	labelText->setColor(fontSizeColor);
	labelText->setAlignment(osgText::Text::CENTER_CENTER);
	labelText->setFontResolution(1000, 1000);
	labelText->setText(label);
	billboard->addDrawable(labelText);

}

void GraphModelEdge::relocate()
{
	SymbolNode *s1 = (*nodeMapId)[src];
	osg::Vec3 p1 = s1->pos;
	SymbolNode *s2 = (*nodeMapId)[dst];
	osg::Vec3 p2 = s2->pos;
	osg::Vec3 pInc = p2-p1;
	osg::Vec3 pIncNorm = pInc;
	pIncNorm.normalize();
	p1 = p1 + pIncNorm*RADIUS;
	p2 = p2 - pIncNorm*RADIUS;
	pInc = p2 - p1;
	float length = pInc.length();
	osg::Vec3 ii = p2 - p1;
	ii.normalize();
	osg::Quat quat = quaternionFromInitFinalVector(osg::Vec3(0, 0, 1), ii);
	if (length <= 0.000001)
	{
		printf("hiuhwhuhhuwfqw\n");
		exit(1);
	}
	float effectiveLength = length-TIPSIZE;
	osg::Vec3 position(((p1+p2)/2.f)-(pIncNorm*TIPSIZE));
	// Set line position/rotation
	line->set(position, RADIUS*0.2, effectiveLength);
	line->setRotation(quat);
	lineDrawable->dirtyDisplayList();
	// Set tip position/rotation
	tip->set(p2-pIncNorm*(TIPSIZE+4), 2.*RADIUS/3., 3 *TIPSIZE);
	tip->setRotation(quat);
	tipDrawable->dirtyDisplayList();
	
	billboard->setPosition(0, (p1+p2)/2.f);
}



GraphModelViewer::GraphModelViewer(osgViewer::ViewerBase::ThreadingModel threadingModel, bool autoUpdate) : QWidget()
{
	setThreadingModel(threadingModel);

	// disable the default setting of viewer.done() by pressing Escape.
	setKeyEventSetsDone(0);

	group = new osg::Group();

	QWidget* widget1 = addViewWidget( createGraphicsWindow(0,0,100,100), group );
	QGridLayout* grid = new QGridLayout;
	grid->addWidget(widget1, 0, 0 );
	setLayout(grid);

	connect(&timer, SIGNAL(timeout()), this, SLOT(update()));
	if (autoUpdate)
		connect(&timer, SIGNAL(timeout()), this, SLOT(animateStep()));
	timer.start(10);
}

void GraphModelViewer::addNode(std::string id, std::string stype)
{
	SymbolNode *s;
	s = new SymbolNode(id, stype);
	s->setPosition(0., 0., 0.);
	group->addChild(s);
	nodeMapId[id] = s;
	nodeVector.push_back(s);
}

void GraphModelViewer::setNodePosition(std::string id, osg::Vec3 np)
{
	nodeMapId[id]->setPosition(np);
}

void GraphModelViewer::addEdge(std::string src, std::string dst, std::string label)
{
// 	printf ("(%s)---[%s]--->(%s)\n", src.c_str(), dst.c_str(), label.c_str());

	GraphModelEdge *edge;
	edge = new GraphModelEdge(src, dst, label, &nodeMapId);
	group->addChild(edge);
	edges.push_back(edge);
}



QWidget *GraphModelViewer::addViewWidget(osgQt::GraphicsWindowQt* gw, osg::Node* scene )
{
	osgViewer::View* view = new osgViewer::View;
	addView( view );

	osg::Camera* camera = view->getCamera();
	camera->setGraphicsContext(gw);

	const osg::GraphicsContext::Traits* traits = gw->getTraits();

	camera->setClearColor( osg::Vec4(0.2, 0.2, 0.6, 1.0) );
	camera->setViewport( new osg::Viewport(0, 0, traits->width, traits->height) );
	camera->setProjectionMatrixAsPerspective(30.0f, static_cast<double>(traits->width)/static_cast<double>(traits->height), 0.01f, 1000000000.0f );

	view->setSceneData( scene );
	view->addEventHandler( new osgViewer::StatsHandler );
	view->setCameraManipulator( new osgGA::TrackballManipulator );

	return gw->getGLWidget();
}

osgQt::GraphicsWindowQt *GraphModelViewer::createGraphicsWindow(int x, int y, int w, int h, const std::string& name, bool windowDecoration)
{
	osg::DisplaySettings* ds = osg::DisplaySettings::instance().get();
	osg::ref_ptr<osg::GraphicsContext::Traits> traits = new osg::GraphicsContext::Traits;
	traits->windowName = name;
	traits->windowDecoration = windowDecoration;
	traits->x = x;
	traits->y = y;
	traits->width = w;
	traits->height = h;
	traits->doubleBuffer = true;
	traits->alpha = ds->getMinimumNumAlphaBits();
	traits->stencil = ds->getMinimumNumStencilBits();
	traits->sampleBuffers = ds->getMultiSamples();
	traits->samples = ds->getNumMultiSamples();

	return new osgQt::GraphicsWindowQt(traits.get());
}

void GraphModelViewer::paintEvent( QPaintEvent* event )
{
	frame();
}


void GraphModelViewer::animateStep()
{
	const float T = 1;
	
	// Update repulsion-induced force
	// For each symbol
	for (uint32_t symbol1=0; symbol1<nodeVector.size(); symbol1++)
	{
		// Initialize forces
		osg::Vec3 force(0,0,0);
		// Compute force sum
		for (uint32_t symbol2=0; symbol2<nodeVector.size(); symbol2++)
		{
			osg::Vec3 inc = nodeVector[symbol2]->pos - nodeVector[symbol1]->pos;
			osg::Vec3 incNorm = inc;
			incNorm.normalize();
			const float dist = inc.length();
			if (symbol1 == symbol2)
			{
				continue;
			}
			/// Repulsion
			force -= incNorm*(1./(dist*dist))*(1000000);
		}
		// Integrate
		nodeVector[symbol1]->vel += force * T;
	}

	// Update link-induced forces
	// For each link
	for (uint32_t edgeIdx=0; edgeIdx<edges.size(); edgeIdx++)
	{
		osg::Vec3 inc = nodeMapId[edges[edgeIdx]->dst]->pos - nodeMapId[edges[edgeIdx]->src]->pos;
		osg::Vec3 incNorm = inc;
		incNorm.normalize();
		const float dist = inc.length();
		if (edges[edgeIdx]->dst == edges[edgeIdx]->src)
		{
			continue;
		}
		/// Spring
		if (dist>10.*RADIUS)
		{
			nodeMapId[edges[edgeIdx]->src]->vel += incNorm*dist*(0.001) * T;
			nodeMapId[edges[edgeIdx]->dst]->vel -= incNorm*dist*(0.001) * T;
		}
	}

	// Update the velocity and position of the nodes
	for (uint32_t symbol1=0; symbol1<nodeVector.size(); symbol1++)
	{
		// Friction
		nodeVector[symbol1]->vel *=  0.993;
		// Update position
		nodeVector[symbol1]->setPosition(nodeVector[symbol1]->pos + nodeVector[symbol1]->vel*T);
	}
	
	// Relocate edges
	relocateEdges();
}

