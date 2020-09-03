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

var rawRoot = 's3-us-west-2.amazonaws.com/usgs-lidar-public/';
var root = 'https://' + rawRoot;
var agRoot = 'https://d1xx504zn7lvnb.cloudfront.net/';
var cfRoot = 'https://d2ywgo0ycqxchv.cloudfront.net/';
var postfix = '&m=5&cf=%5B7,49%5D';

var commify = (n) => {
    var commifyInt = (n) => n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    var split = n.toString().split('.');
    return commifyInt(split[0]) +
        (split.length == 2 ? '.' + split[1].substring(0, 2) : '');
};

var potreeLinkify = (name) => '/data/view.html?r=' + root + name + postfix;

var cesiumLinkify = (name) => `http://cesium.entwine.io/?url=http://usgs-3dtiles.entwine.io/${name}/ept-tileset/tileset.json`

var plasioLinkify = (name) => 'http://dev.speck.ly/?s=0&r=ept://' +
    rawRoot + name + '&c0s=remote%3A%2F%2Fimagery%3Furl%3Dhttp%253A%252F%252Fserver.arcgisonline.com%252FArcGIS%252Frest%252Fservices%252FWorld_Imagery%252FMapServer%252Ftile%252F%257B%257Bz%257D%257D%252F%257B%257By%257D%257D%252F%257B%257Bx%257D%257D.jpg';

var Resource = React.createClass({
    render: function() {
        var entry = this.props.entry;
        var name = entry.name;
        var points = entry.points;

        var potree = potreeLinkify(name);
        var cesium = cesiumLinkify(name);
        // '/data/view.html?r=' + root + name + postfix;
            // 'http://dev.speck.ly/?s=0&r=ept://' + rawRoot + name +
            // '&c0s=remote%3A%2F%2Fimagery%3Furl%3Dhttp%253A%252F%252Fserver.arcgisonline.com%252FArcGIS%252Frest%252Fservices%252FWorld_Imagery%252FMapServer%252Ftile%252F%257B%257Bz%257D%257D%252F%257B%257By%257D%257D%252F%257B%257Bx%257D%257D.jpg';
        var link = <i className='fa fa-circle'></i>;

        var ept = root + name + '/ept.json';
        var style = { minWidth: 64 }

        return <tr>
            <td>
                <a href={ potree }>
                    { name }
                </a>
            </td>
            <td className='text-right'>
                { commify(points) }
            </td>
            <td className='text-center' style={ style }><a href={ potree }>{ link }</a></td>
            <td className='text-center' style={ style }><a href={ cesium }>{ link }</a></td>
            <td className='text-center' style={ style }><a href={ ept }>{ link }</a></td>
        </tr>;
    }
});

var Column = { Name: 0, Points: 1 };
var Order = { Asc: 0, Desc: 1 };

var colors = [
    "#e6194B", "#3cb44b", "#ffe119", "#4363d8", "#f58231", "#911eb4", "#42d4f4",
    "#f032e6", "#bfef45", "#fabebe", "#469990", "#e6beff", "#9A6324", "#fffac8",
    "#800000", "#aaffc3", "#808000", "#ffd8b1", "#000075", "#a9a9a9"
];

var Resources = React.createClass({
    getInitialState() {
        return {
            text: '',
            sortCol: Column.Name,
            sortOrder: Order.Asc,
            polygons: { }
        };
    },
    render() {
        var op = this.state.sortOrder == Order.Asc
            ? (a, b) => a < b
            : (a, b) => a > b;

        var re = new RegExp(this.state.text);
        var resources = this.props.resources.filter((r) => r.name.match(re))
        .sort((a, b) => {
            if (this.state.sortCol == Column.Name) {
                a = a.name;
                b = b.name;
            }
            else {
                a = a.points;
                b = b.points;
            }

            return op(a, b) ? -1 : 1;
        });

        var points = resources.reduce((p, c) => p + c.points, 0);

        var multi = null;
        if (resources.length > 1 && resources.length <= 30) {
            var link = '/data/view.html?r=[' + resources.reduce((p, c, i) => {
                return p + (i ? ',' : '') + '"' + root + c.name + '"';
            }, '') + ']' + postfix;

            var ag = link.replace(new RegExp(root, 'g'), agRoot)
            var cf = link.replace(new RegExp(root, 'g'), cfRoot)
            multi = <div className='text-center'>
                <a href={ link }>View selected</a>
            </div>;
        }

        var resourceHeader = 'Name';
        var pointsHeader = 'Points';
        var symbol = this.state.sortOrder == Order.Asc ? ' ↓' : ' ↑';
        if (this.state.sortCol == Column.Name) resourceHeader += symbol;
        else pointsHeader += symbol;
        var headerStyle = { color: 'black' };

        return <div>
            <div className='text-center'>
                <p>
                    <strong>{ commify(points) }</strong> points
                    in <strong>{ commify(resources.length) }</strong> resources
                </p>
            </div>
            <div id="map" className='center-block' style={ {
                height: 460,
                maxWidth: '80%',
                boxShadow: '0 0 2px #888'
            } }/>
            <br/>
            <div className='row'>
                <div className='col-xs-1 col-sm-3'/>
                <div className='form-group col-xs-10 col-sm-6 center-block'>
                    <input
                        placeholder='Filter'
                        className='center-block form-control col-xs-12 col-sm-6'
                        type='text'
                        value={ this.state.text }
                        onChange={ this.textChanged }
                    />
                </div>
                <div className='col-xs-1 col-sm-3'/>
            </div>
            <table className='table table-striped table-fit table-bordered'>
                <thead>
                    <tr>
                        <th className='text-center'>
                            <a
                                href='#'
                                style={ headerStyle }
                                onClick={ () => this.sort(Column.Name) }
                            >
                                { resourceHeader }
                            </a>
                        </th>
                        <th className='text-center'>
                            <a
                                href='#'
                                style={ headerStyle }
                                onClick={ () => this.sort(Column.Points) }
                            >
                                { pointsHeader }
                            </a>
                        </th>
                        <th className='text-center'>Potree</th>
                        <th className='text-center'>Cesium</th>
                        <th className='text-center'>EPT</th>
                    </tr>
                </thead>
                <tbody>
                {
                    resources.map((v, i) => <Resource key={ i } entry={ v }/>)
                }
                </tbody>
            </table>
            { multi }
        </div>;
    },
    sort(col) {
        var order = this.state.sortOrder;

        if (col == this.state.sortCol) {
            // If we're sorting by the same column, flip the order.
            order = order == Order.Asc ? Order.Desc : Order.Asc;
        }
        else {
            // Otherwise, set to ascending in our new column.
            order = Order.Asc;
        }

        this.setState({ sortCol: col, sortOrder: order });
    },
    textChanged(e) {
        var text = e.target.value;
        var re = new RegExp(text);
        var polygons = Object.keys(this.state.polygons).reduce((p, name) => {
            var v = {
                visible: this.state.polygons[name].visible,
                polygon: this.state.polygons[name].polygon,
            };

            var toBeVisible = name.match(re);

            if (v.visible != toBeVisible) {
                if (toBeVisible) v.polygon.addTo(this.map);
                else v.polygon.removeFrom(this.map);
            }

            v.visible = toBeVisible;
            p[name] = v;
            return p;
        }, { });

        this.setState({ text: text, polygons: polygons });
    },
    componentDidMount() {
        this.map = L.map('map', { attributionControl: false })
        .setView([39.0902, -94.2871], 4);

        // watercolor, toner, terrain
        //   var layer = new L.StamenTileLayer('terrain');
        var layer = L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg', {
            opacity: 0.8
        });
        this.map.addLayer(layer);


        let i = 0
        const polygons = []
        L.geoJSON(this.props.boundaries, {
            style: (feature) => ({
                color: colors[i++ % colors.length],
                weight: 2,
                fillOpacity: .7
            }),
            onEachFeature: (feature, layer) => {
                const name = feature.properties.name
                layer
                .bindTooltip('<strong>' + name + '</strong>', { sticky: true })
                .bindPopup('<div>' +
                    '<strong>' + name + '</strong>' +
                    '<br>' +
                    '(<a href="' + potreeLinkify(name) + '">Potree</a>)' +
                '</div>', { });

                polygons[name] = { visible: true, polygon: layer}
            }
        }).addTo(this.map)
        this.setState({ polygons })
    },
})

var ajax = function(method, subpath, data) {
    if (subpath[0] != '/') subpath = '/' + subpath;
    return $.ajax({
        type: method.toUpperCase(),
        url: window.location.origin + subpath,
        data: method == 'get' ? data : JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json; charset=utf-8'
    })
};

var Page = React.createClass({
    getInitialState() {
        return { resources: null, boundaries: null }
    },
    componentDidMount() {
        ajax('get', 'boundaries/resources.geojson')
        .done((boundaries) => this.setState({
            boundaries,
            resources: boundaries.features.reduce((o, b) => [
                ...o,
                { name: b.properties.name, points: b.properties.count }
            ], [])
        }))
    },
    render() {
        const { resources, boundaries } = this.state;

        var contents = resources
            ? <Resources resources={ resources } boundaries={ boundaries }/>
            : <i className='center-block'>Loading...</i>;

        return <div>
            <Header/>
                <div className='container-fluid'>
                    <div className='row'>
                        <div
                            className='col-xs-12'
                            style={ { paddingBottom: 64 } }
                        >
                            <h2
                                className='center-block row'
                                style={ {
                                    color: '#192854',
                                    paddingTop: 36,
                                    paddingBottom: 24
                                } }
                            >
                                USGS
                                <span style={ { color: '#39B44A' } }> / </span>
                                Entwine
                            </h2>
                            { contents }
                        </div>
                    </div>
                </div>
            <Footer/>
        </div>;
    }
});

ReactDOM.render(<Page/>, document.getElementById('app'));

