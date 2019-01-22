var Nav = React.createClass({
    render: function() {
        return <div className='col-xs-12 col-sm-5' id='navbar'>
            <ul
                id='navbarUl'
                className=
                    'nav navbar-nav navbar-right nav-pills'
            >
                <li>
                    { this.props.children }
                </li>
            </ul>
        </div>;
    }
});

var Header = React.createClass({
    render: function() {
        return (
            <div className='navbar navbar-default' id='header'>
                <div className='container-fluid'>
                    <div className='row'>
                        <div className='col-xs-12 col-sm-7'>
                            <a href='/'>
                                <img
                                    id='banner'
                                    src='resources/images/banner.png'
                                />
                            </a>
                        </div>
                        <Nav>
                            <a href='/about.html'>
                                <span style={ { color: '#888' } }>
                                    About
                                </span>
                            </a>
                        </Nav>
                    </div>
                </div>
            </div>
        );
    }
});

var Footer = React.createClass({
    render: function() {
        return (
            <footer className='footer'>
                <div className='container-fluid'>
                    <div className='footer-content'>
                        <div className='row'>
                            <div className='col-xs-5'></div>
                            <div className='col-xs-2'>
                                <a href='/'>
                                    <img
                                        className='center-block'
                                        id='footer-icon'
                                        src='resources/images/entwine-logo.png'
                                    />
                                </a>
                            </div>
                            <div className='col-xs-5'>
                                <p id='copyright'>
                                    Entwine © Hobu, Inc.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </footer>
        );
    }
});

var Credit = React.createClass({
    render: function() {
        return <div className='row'>
            <div className='col-xs-12 col-sm-4'/>
            <div className='col-xs-12 col-sm-4 center-text'>
                <h4>{ this.props.name }</h4>
                <p>{ this.props.children }</p>
            </div>
            <div className='col-xs-12 col-sm-4'/>
        </div>;
    }
});

var Content = React.createClass({
    render: function() {
        return <div className='center-block lead row'>
            <p>
                <a href="https://www.usgs.gov/">USGS</a> LiDAR data made available by the <a href="https://aws.amazon.com/opendata/public-datasets/">AWS Public Dataset Program</a>
            </p>
            <p>This website provides Potree and Plasio.js interfaces to the
AWS USGS LiDAR Public Dataset. More information about this dataset
can be found at https://registry.opendata.aws/usgs-lidar/ and
at its GitHub page at https://github.com/hobu/usgs-lidar/
    </p>

            <p>
            Provided as EPT resources created with <a href="https://entwine.io">Entwine</a>.
            </p>
        </div>
    }
});

var Credits = React.createClass({
    render() {
        return <div className='center-block lead row'>
            <p>
                Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.
            </p>
        </div>;
    }
});

var Page = React.createClass({
    render: function() {
        return <div>
            <Header/>
                <div className='container-fluid'>
                    <div className='row'>
                        <div
                            className='col-xs-12'
                            style={ { paddingBottom: 64 } }
                        >
                            <h2
                                className='center-block'
                                style={ {
                                    color: '#192854',
                                    paddingTop: 36,
                                    paddingBottom: 48
                                } }
                            >
                                USGS
                                <span style={ { color: '#39B44A' } }> / </span>
                                Entwine
                            </h2>
                            <h3
                                className='center-block'
                                style={ { color: '#192854', paddingBottom: 24 } }
                            >
                                About
                            </h3>
                            <Content/>
                            <br/>
                            <h3
                                className='center-block'
                                style={ { color: '#192854', paddingBottom: 24 } }
                            >
                                Credits
                            </h3>
                            <Credits/>
                        </div>
                    </div>
                </div>
            <Footer/>
        </div>;
    }
});

ReactDOM.render(<Page/>, document.getElementById('app'));

