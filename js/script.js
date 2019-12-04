var maybeParse = function(key, val) {
    if (['r', 'resource', 'location'].includes(key)) {
        if (val[0] == '[') return JSON.parse(val);
        if (val[0] != '"') return val;
    }
    return JSON.parse(val);
};

var queryParam = function(name) {
    name = name.replace(/[\[\]]/g, '\\$&');
    var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)');
    var results = regex.exec(window.location.href);
    if (!results) return null;
    if (!results[2]) return true;

    return maybeParse(name, decodeURIComponent(results[2].replace(/\+/g, ' ')));
}

var Vec = (x, y, z) => {
    if (Array.isArray(x)) return new THREE.Vector3(x[0], x[1], x[2]);
    else return new THREE.Vector3(x, y, z);
};

var addAnnotation = (v) => {
    viewer.scene.addAnnotation(Vec(v.pos), {
        title: v.name,
        cameraPosition: Vec(v.cpos),
        cameraTarget: Vec(v.ctgt),
        actions: v.actions
    });
};

var mobileRegex =
    /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
var mobile = mobileRegex.test(navigator.userAgent);
if (mobile) console.log('Using mobile settings');

var defaults = {
    pointBudget: mobile ? 700 * 1000 : 3.5 * 1000 * 1000,
    edlEnabled: !mobile,
    edlStrength: 0.2,
    edlRadius: 1.4,
    pointSize: 3,
    pointType: Potree.PointSizeType.FIXED,
    pointShape: Potree.PointShape.SQUARE,
    material: Potree.PointColorType.INTENSITY_GRADIENT,
    intensityRange: [0, 65536],
    weightClassification: 1,
    fov: 80,
    opacity: 1,
    rgbGamma: 1,
    rgbContrast: 0,
    rgbBrightness: 0,
    intensityGamma: 1,
    intensityContrast: 0,
    intensityBrightness: 0,
    classificationFilter: [],
    hq: true
}

var clone = (v) => JSON.parse(JSON.stringify(v));

var setAll = (f) => viewer.scene.pointclouds.forEach((pc) => f(pc));

var lookup = {
    r: 'resource',
    m: 'material',
    cg: 'rgbGamma',
    cc: 'rgbContrast',
    cb: 'rgbBrightness',
    ig: 'intensityGamma',
    ic: 'intensityContrast',
    ib: 'intensityBrightness',
    ps: 'pointSize',
    pt: 'pointType',
    ph: 'pointShape',
    op: 'opacity',
    edl: 'edlEnabled',
    er: 'edlRadius',
    es: 'edlStrength',
    pb: 'pointBudget',
    sbb: 'showBoundingBox',
    p: 'position',
    t: 'target',
    bg: 'background',
    ir: 'intensityRange',
    era: 'elevationRange',
    cf: 'classificationFilter',
    l: 'language',
    d: 'description',
    wc: 'weightClassification',
    hq: 'hq'
};

var getDefault = (key) => config[key] || defaults[key];
var maybe = (key, val) => {
    // If the value is not equal to the default for this key, return the value.
    // Otherwise return null.

    var d = getDefault(key);

    if (Array.isArray(val)) {
        if (!d || val.some((v, i) => v != d[i])) return val;
        else return null;
    }
    return val != getDefault(key) ? val : null;
};

var getClassificationFilters = () => {
    var list = viewer.scene.pointclouds[0].material.classification;
    return Object.keys(list).reduce((p, c, i) => {
        if (c != 'DEFAULT' && !list[c].w) return p.concat(parseInt(c));
        else return p;
    }, []);
};

var get = () => {
    var pc = viewer.scene.pointclouds[0];
    var mt = pc.material;

    console.log('CONFIG', config);
    console.log('DEFAULTS', defaults);

    var state = {
        // Include these if they've changed from the initial state.
        m: maybe('material', mt.pointColorType),
        ps: maybe('pointSize', mt.size),
        pt: maybe('pointType', mt.pointSizeType),
        ph: maybe('pointShape', mt.shape),
        fov: maybe('fov', viewer.fov),
        op: maybe('opacity', mt.opacity),
        edl: maybe('edlEnabled', viewer.getEDLEnabled()),
        er: maybe('edlRadius', viewer.getEDLRadius()),
        es: maybe('edlStrength', viewer.getEDLStrength()),
        ir: maybe('intensityRange',
                [mt.intensityRange[0], mt.intensityRange[1]]),
        era: maybe('elevationRange',
                [mt.elevationRange[0], mt.elevationRange[1]]),
        cg: maybe('rgbGamma', mt.rgbGamma),
        cc: maybe('rgbContrast', mt.rgbContrast),
        cb: maybe('rgbBrightness', mt.rgbBrightness),
        ig: maybe('intensityGamma', mt.intensityGamma),
        ic: maybe('intensityContrast', mt.intensityContrast),
        ib: maybe('intensityBrightness', mt.intensityBrightness),

        cf: maybe('classificationFilter', getClassificationFilters()),
        hq: maybe('hq', viewer.useHQ),

        // Always include these.
        p: viewer.scene.view.position.toArray(),
        t: viewer.scene.view.getPivot().toArray(),

        // For these, only include them if they are query overrides.
        r: queryParam('r') || queryParam('resource'),
    };

    return Object.keys(state).reduce((p, k) => {
        if (state[k] != null) p[k] = state[k];
        return p;
    }, { });
};

var set = (k, v) => {
    switch (k) {
        case 'fov':
            viewer.setFOV(v);
            break;
        case 'material':
            setAll((pc) => pc.material.pointColorType = v);
            break;
        case 'pointSize':
            setAll((pc) => pc.material.size = v);
            break;
        case 'pointType':
            setAll((pc) => pc.material.pointSizeType = v);
            break;
        case 'pointShape':
            setAll((pc) => pc.material.shape = v);
            break;
        case 'opacity':
            setAll((pc) => pc.material.opacity = v);
            break;
        case 'edlEnabled':
            viewer.setEDLEnabled(v);
            break;
        case 'edlRadius':
            viewer.setEDLRadius(v);
            break;
        case 'edlStrength':
            viewer.setEDLStrength(v);
            break;
        case 'pointBudget':
            viewer.setPointBudget(v);
            break;
        case 'showBoundingBox':
            viewer.setShowBoundingBox(v);
            break;
        case 'position':
            viewer.scene.view.position.set(v[0], v[1], v[2]);
            break;
        case 'target':
            viewer.scene.view.lookAt(new THREE.Vector3(v[0], v[1], v[2]));
            break;
        case 'background':
            viewer.setBackground(v);
            break;
        case 'intensityRange':
            setAll((pc) => pc.material.intensityRange = [v[0], v[1]]);
            break;
        case 'elevationRange':
            setAll((pc) => pc.material.elevationRange = [v[0], v[1]]);
            break;
        case 'rgbGamma':
            setAll((pc) => pc.material.rgbGamma = v);
            break;
        case 'rgbContrast':
            setAll((pc) => pc.material.rgbContrast = v);
            break;
        case 'rgbBrightness':
            setAll((pc) => pc.material.rgbBrightness = v);
            break;
        case 'intensityGamma':
            setAll((pc) => pc.material.intensityGamma = v);
            break;
        case 'intensityContrast':
            setAll((pc) => pc.material.intensityContrast = v);
            break;
        case 'intensityBrightness':
            setAll((pc) => pc.material.intensityBrightness = v);
            break;
        case 'weightClassification':
            setAll((pc) => pc.material.weightClassification = v);
            break;
        case 'classificationFilter':
            break;
            for (var i = 0; i < v.length; ++i) {
                console.log('CLA', i, v[i]);
                var c = document.getElementById('chkClassification_' + v[i]);
                viewer.setClassificationVisibility(v[i], false);
                if (c) {
                    c.checked = false;
                    viewer.setClassificationVisibility(v[i], false);
                }
            }
            break;
        case 'language':
            viewer.setLanguage(v);
            break;
        case 'description':
            viewer.setDescription(v);
            break;
        case 'annotations':
            v.forEach(addAnnotation);
            break;
        case 'hq':
            viewer.useHQ = !!v;
        case 'resource':
        case 'location':
        case 'debug':
            break;
        default:
            console.log('Unrecognized query parameter:', k);
            break;
    }
};

var queryConfig = function() {
    // Extract configuration params from the query string.
    var result = { };
    var qs = window.location.search;
    if (!qs) return result;

    var tokens = qs.substring(1).split('&');
    var decode = (v) => decodeURIComponent(v).trim();

    tokens.forEach((c) => {
        if (c.indexOf('=') == -1) result[decode(c)] = true;
        else {
            var keyVal = c.split('=');
            var key = decode(keyVal[0]);
            var val = maybeParse(key, decode(keyVal[1]));

            result[key] = val;
        }
    }, { });

    return result;
}

window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));

var error = (message) => { throw new Error(message); };

if (!config) error('No config supplied');
var resources = config.resource || queryParam('r') || queryParam('resource');
if (!resources) error('No resource supplied');
if (!Array.isArray(resources)) resources = [resources];

var appendSlash = (path) => path.endsWith('/') ? path : path + '/';
var normalizePath = (p) => {
    var path = p;
    var name = null;

    if (path.startsWith('greyhound://')) {
        path = appendSlash(path);
        name = path.match(/\/resource\/(.+)/)[1];
        return [path, name];
    }

    if (!path.endsWith('ept.json')) {
        path = appendSlash(path) + 'ept.json';
        if (!path.startsWith('http') && !path.startsWith('/')) {
            path = 'http://' + path;
        }
    }

    name = path.replace('/ept.json', '').split('/').pop();
    return [path, name];
};

var pcs = new Array(resources.length).fill(null);

var init = (name) => {
    console.log('Applying configuration');

    // Merge the config in increasing priority from:
    //  - defaults
    //  - configuration
    //  - query parameters
    //
    // Also replace any shorthand names with the full parameter name.
    var merge = (a, b) => {
        Object.keys(b).forEach((key) => {
            var val = b[key];
            if (lookup[key]) key = lookup[key];
            a[key] = val;
        });
        return a;
    };

    var active = merge(clone(defaults), merge(clone(config), queryConfig()));
    console.log('Active', active);

    // Sort these purely because position must be applied before target or the
    // resulting view will be wrong.
    Object.keys(active).sort().forEach((k) => {
        var v = active[k];
        set(k, v);
    });

    if (!active.position || !active.target) {
        console.log('Fitting to screen');
        try { viewer.fitToScreen(); } catch (e) { }
    }

    var r = queryParam('r') || queryParam('resource');
    if (r) r = '?r=' + JSON.stringify(r);
    else r = ''
    history.replaceState(null, null, location.pathname + r);

    console.log('Loading UI');

    viewer.loadGUI(() => {
        viewer.setLanguage('en');
        $("#menu_appearance").next().show();
        $("#menu_scene").next().show();
        if (name) $("a:contains('" + name + "')").click();

        if (typeof(Storage) !== 'undefined') {
            var pb = parseInt(localStorage.getItem('pointBudget'));
            if (Number.isInteger(pb)) {
                console.log('Setting pointBudget from localStorage');
                viewer.setPointBudget(pb);
            }
        }

        viewer.addEventListener('point_budget_changed', (e) => {
            if (typeof(Storage) !== 'undefined') {
                console.log('Storing pointBudget');
                localStorage.setItem('pointBudget', viewer.getPointBudget());
            }
        });

        window.viewerLoaded = true;

        active.classificationFilter.forEach((v) => {
            var c = document.getElementById('chkClassification_' + v);
            if (c) {
                console.log('UNCHECK');
                c.checked = false;
                viewer.setClassificationVisibility(v, false);
            }
        });
    });
};

resources.forEach((p, i) => {
    var [path, name] = normalizePath(p);
    console.log('Loading', name, path);

    Potree.loadPointCloud(path, name, (e) => {
        pcs[i] = e.pointcloud;
        console.log('Loaded', name, i);
        viewer.scene.addPointCloud(e.pointcloud);

        if (pcs.every((v) => v)) {
            console.log('All point clouds loaded');
            init(resources.length == 1 ? name : null);

            if (window.config.color &&
                window.config.color.length == resources.length) {
                var fromRgb = function(a) {
                    a = a.map(v => v / 255)
                    return { r: a[0], g: a[1], b: a[2] }
                }
                for (var c = 0; c < resources.length; ++c) {
                    viewer.scene.pointclouds[c].material.color =
                        fromRgb(window.config.color[c])
                }
            }
        }
    });
});

new Clipboard('#entwine_copy', {
    text: function() {
        var state = get();
        var keys = Object.keys(state);
        var moveToFront = function(k) {
            if (state[k]) keys = [k].concat(keys.filter((v) => v != k));
        };
        moveToFront('r');
        moveToFront('b');
        moveToFront('p');
        moveToFront('t');
        var q = keys.reduce((p, k) => {
            return p + (p.length ? '&' : '?') +
                k + '=' + JSON.stringify(state[k]);
        }, '');

        return window.location.origin + window.location.pathname + encodeURI(q);
    }
});

window.toggleAnnotations = () => {
    var el = $('#entwine_toggle');
    var turningOn = el.attr('state') == 'off';

    if (turningOn) {
        $('.annotation').each(function() { $(this).removeClass('display_none') })
        el.attr('state', 'on');
        el.attr('src', '/resources/icons/entwine-annotations-on.svg');
    }
    else {
        $('.annotation').each(function() { $(this).addClass('display_none') })
        el.attr('state', 'off');
        el.attr('src', '/resources/icons/entwine-annotations-off.svg');
    }
}

