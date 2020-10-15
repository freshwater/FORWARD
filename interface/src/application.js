
"🎲 ⚀ ⚁ ⚂ ⚃ ⚄ ⚅";

let clientId = new String(Math.random()).substring(2);

class DownloadsSelection extends React.Component {
    render() {
        return <select id={this.props.id} defaultValue={this.props.initialValue}
                        onChange={(event) => this.props.onChange}> {
                this.props.values .map (
                    (value) => <option value={value} key={value}>{value}</option>
                ) }
        </select>;
    }
}

/*let downloadId = new String(Math.random()).substring(2);
ReactDOM.render([<DownloadsSelection id={downloadId} values={[".mp4 Replay Video", ".bk2 Replay Data", ".json Action Sequence"]}
                                        initialValue=".mp4 Replay Video" />,
                    <span>&nbsp;</span>,
                    <button onClick={(event) => download(document.getElementById(downloadId).value, event)}>Download</button>],
                document.querySelector('.downloads-selection'));*/

class DataDisplay extends React.Component {
    render() {
        let {Type: type, Value: value, ...object} = this.props.data;

        if (type === "List") {
            return <div className="list">
                {value .map ((element, index) => <DataDisplay data={element} key={index} index={index} globalState={globalState} />)}
            </div>;

        } else if (type === "Dictionary") {
            return <table className="dictionary">
                <tbody>
                    { /* Keys and values can be arbitrary structures. For now just use index as UI key. */}
                    {value .map (([key1, value1], index) => <tr key={index}>
                        <td className="key"><DataDisplay data={key1} globalState={globalState} /></td>
                        <td className="value"><DataDisplay data={value1} globalState={globalState} /></td>
                    </tr>)}
                </tbody>
            </table>;

        } else if (type === "Image") {
            let {Shape: shape, DisplayScale: displayScale, Elements: elements} = object;

            return <div key={this.props.index} className="image-container" style={{position: 'relative', display: 'inline-block'}}>
                <div className="image">
                    <img src={value} className="image" style={{imageRendering: 'pixelated'}}
                                     height={displayScale*shape[0]} width={displayScale*shape[1]}
                                     onClick={(event) => this.props.globalState.onClick(event, {Value: value, ...object})}
                                     onMouseMove={(event) => this.props.globalState.onMouseMove(event, {Value: value, ...object})} />
                </div>

                { elements .map ( ({Type: type,
                                    Geometry: [[x1, y1], [x2, y2]], Color: [r, g, b, a],
                                    Label: label, LabelColor: [r2, g2, b2, a2]}, index) => {

                    [x1, y1, x2, y2] = [displayScale*x1, displayScale*y1, displayScale*x2, displayScale*y2];

                    return <span key={`region-${index}`} className="region" style={{
                                        position: 'absolute',
                                        left: x1, top: y1,
                                        width: x2 - x1,
                                        height: y2 - y1,
                                        fontSize: '0.5em',
                                        overflow: 'hidden',

                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',

                                        background: `rgba(${r*255}, ${g*255}, ${b*255}, ${a})`,
                                        color: `rgba(${r2*255}, ${g2*255}, ${b2*255}, ${a2})`}}>{label}</span>;
                } ) }
            </div>;

        } else if (type === "Number") {
            return <span key={this.props.index} className="number">{value}</span>;

        } else if (type === "String") {
            return <span key={this.props.index} className="string">{value}</span>;

        } else if (type === "Array2D") {
            let rowText = (row) => `[${row}]`;

            let height = value.length;
            let width = value.length > 0 ? value[0].length : 0;

            let clipboardText = `z = np.array([\n${value .map (rowText) .join(",\n")}])`;
            value = value.concat([Array(width).fill(" ")]);

            if (height*width > 0) {
                value[height - 1 + 1][width - 1] = <span className="clipboard-button" title="Copy to Clipboard" onClick={(event) => clipboardCopy(clipboardText, event)}>📋</span>;
            }

            return <table key={this.props.index} className="array">
                <tbody>
                {value .map ( (row, i) => <tr key={i}>{row .map ((elem, j) => <td key={j}>{elem}</td> )}</tr>)}
                </tbody>
            </table>;

        } else if (type === "ArrayPlot3D") {
            return <ArrayPlot3D data={this.props.data} />;

        } else if (type === "Button") {
            let { Id: id } = object;

            let onClick = function () {
                query({
                    "Request": "Event",
                    "ClientId": clientId,
                    "Type": "Button_OnClick",
                    "Id": id
                }, function (response) {
                    // console.log("r.", performance.now() - t0);
                    setDisplay(response['Data']);
                });
            };

            return <button id={id} key={id} className="button" onClick={onClick}>{value}</button>

        } else if (type === "SelectionList") {
            return <SelectionList data={this.props.data} />;

        } else if (type === "CheckList") {
            return <CheckList data={this.props.data} />;

        } else if (type === "NumberInput") {
            let {Label: label, Id: id, Minimum: min, Maximum: max, Value: value} = this.props.data;
            let onChange = function (event) {
                let newValue = event.target.value;
                // event.target.blur();
                query({
                    "Request": "Event",
                    "ClientId": clientId,
                    "Type": "NumberInput_OnChange",
                    "Value": newValue,
                    "Id": id
                }, function (response) {
                    setDisplay(response['Data']);
                });
            };

            return <span style={{display: 'flex', flexDirection: 'row'}}>
                <input type="number" min={min} max={max} value={value}
                    onChange={onChange}></input>
                </span>;

        } else {
            return <div></div>;
        }
    }
}

class SelectionList extends React.Component {
    render() {
        let {Value: options, SelectedValue: selectedOption, Id: id, IsEnabled: enabled} = this.props.data;

        let onChange = function (event) {
            query({
                "Request": "Event",
                "ClientId": clientId,
                "Type": "SelectionList_OnChange",
                "Value": event.target.value,
                "Id": id
            }, function (response) {
                setDisplay(response['Data']);
            });
        };

        return <select defaultValue={selectedOption} onChange={onChange} disabled={!enabled}> {
                options .map ((value) => <option value={value} key={value}>{value}</option>)
        } </select>;
    }
}

class CheckList extends React.Component {
    render() {
        let {Value: options, SelectedValue: selectedOptions, Id: id} = this.props.data;

        let onChange = function (event) {
            let key = event.target.value;
            let newValue = !selectedOptions.includes(key);

            query({
                "Request": "Event",
                "ClientId": clientId,
                "Type": "CheckList_OnChange",
                "Key": key,
                "Value": newValue,
                "Id": id
            }, function (response) {
                setDisplay(response['Data']);
            });
        };

        return <div> {
            options .map ((option) => <span key={option}>
                <input type="checkbox" id={option} name={option} value={option}
                       checked={selectedOptions.includes(option)}
                       onChange={onChange} />
                <label htmlFor={option}>{option}</label>
            </span>)
        } </div>;
    }
}

import * as THREE from './three/three.min.js';
import { OrbitControls } from './three/OrbitControls.js';
import { LightProbeGenerator } from './three/LightProbeGenerator.js';

class ArrayPlot3D extends React.Component {
    constructor() {
        super();
        this.domId = `${Math.random()}`;

        this.initialize = this.initialize.bind(this);
        this.animate = this.animate.bind(this);

        this.scene = new THREE.Scene();
        this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
        this.camera = null;
        this.previousCameraPosition = new THREE.Vector3(0, 0, 0);
        this.mesh = null;
        this.geometry = null;
        this.material = null;

        this.positionsIndices = [];
        this.instanceColorsOriginal = null;
        this.instanceColors = null;
        this.buckets = [];

        this.valueReferences = {};
    }

    componentDidMount() {
        this.initialize();
    }

    initialize() {
        let {Value: array, Shape: shape} = this.props.data;
        let totalCount = shape[0] * shape[1] * shape[2];

        let cubeCamera;

        let domElement = document.getElementById(this.domId);

        materialCreate.bind(this)();
        this.animate();

        function materialCreate() {
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.setSize(domElement.clientWidth, domElement.clientHeight);
            domElement.appendChild(this.renderer.domElement);

            let cubeRenderTarget = new THREE.WebGLCubeRenderTarget( 256, {
                // encoding: THREE.sRGBEncoding,
                format: THREE.RGBAFormat
            } );

            cubeCamera = new THREE.CubeCamera( 1, 1000, cubeRenderTarget );

            let lightProbe = new THREE.LightProbe();
            this.scene.add(lightProbe);

            let urls = ['px', 'nx', 'py', 'ny', 'pz', 'nz'] .map (direction => `three/textures/${direction}.png`)

            new THREE.CubeTextureLoader().load(urls, (cubeTexture) => {
                // cubeTexture.encoding = THREE.sRGBEncoding;
                this.scene.background = cubeTexture;
                cubeCamera.update(this.renderer, this.scene);

                lightProbe.copy(LightProbeGenerator.fromCubeRenderTarget(this.renderer, cubeRenderTarget));
                this.scene.background = new THREE.Color(0xffffff);

                let material = new THREE.MeshStandardMaterial({
                    color: 0xffffff,
                    metalness: 0,
                    roughness: 0,
                    envMap: cubeTexture,
                    envMapIntensity: 1,
                    transparent: true,
                });

                let scale = 100;

                let max = Math.max(...shape);
                let rescale = scale / max;
                let mean0 = rescale * shape[0] / 2;
                let mean1 = rescale * shape[1] / 2;
                let mean2 = rescale * shape[2] / 2;

                let k = scale / max;
                let geometry = new THREE.BoxBufferGeometry(k, k, k);

                material.onBeforeCompile = function (shader) {
                    shader.vertexShader = shader.vertexShader
                        .replace('#include <common>', `attribute vec4 instanceColor;
                                                       varying vec4 vInstanceColor;
                                                       #include <common>`)

                        .replace('#include <begin_vertex>', `#include <begin_vertex>
                                                             vInstanceColor = instanceColor;`);

                    shader.fragmentShader = shader.fragmentShader
                        .replace('#include <common>', `varying vec4 vInstanceColor;
                                                       #include <common>`)

                        .replace('vec4 diffuseColor = vec4( diffuse, opacity );',
                                    `vec4 diffuseColor = vec4( diffuse * vInstanceColor.xyz, vInstanceColor.w );`);
                };

                this.geometry = geometry
                this.material = material

                this.meshCreate();
            });
        };

        this.camera = this.camera || new THREE.PerspectiveCamera(70, domElement.clientWidth / domElement.clientHeight, 1, 10000);
        this.camera.position.x = 120;
        this.camera.position.y = 120;
        this.camera.position.z = 120;

        let controls = new OrbitControls(this.camera, this.renderer.domElement);
        controls.minDistance = 80;
        controls.maxDistance = 340;

        domElement.addEventListener('resize', onWindowResize, false);

        function onWindowResize() {
            this.camera.aspect = domElement.clientWidth / domElement.clientHeight;
            this.camera.updateProjectionMatrix();

            this.renderer.setSize(domElement.clientWidth, domElement.clientHeight);
        }
    }

    animate() {
        requestAnimationFrame(this.animate);

        if (this.mesh === null) {
            return ;
        }

        // Couldn't figure out a depth/blend setting to automatically set
        // the render order as back-to-front from any direction.
        // This will work for now.
        if (!this.camera.position.equals(this.previousCameraPosition) && Math.random() < 1) {
            this.previousCameraPosition.copy(this.camera.position);

            let template = new THREE.Object3D();

            let t0 = performance.now();

            /*
                Bucket sort with number of buckets = n.
            */

            // Find min/max
            let min = 99999;
            let max = -99999;
            this.positionsIndices .forEach (([position], index) => {
                let distance = this.camera.position.distanceTo(position);
                this.positionsIndices[index][2] = distance;
                if (distance < min) { min = distance; }
                if (distance > max) { max = distance; }
            });

            // Bucketize
            this.buckets .forEach ((_, index) => { this.buckets[index] = [] });
            let increment = 1 / this.positionsIndices.length;
            this.positionsIndices .forEach ((tuple) => {
                // ignore fully transparent blocks
                if (this.instanceColorsOriginal[4*tuple[1] + 3] !== 0) {
                    let cameraDistance = tuple[2];
                    cameraDistance = (cameraDistance - min) / (max - min);
                    cameraDistance = 1 - cameraDistance;

                    this.buckets[Math.floor(cameraDistance / increment)].push(tuple);
                }
            });

            // console.log('z.', performance.now() - t0);

            // Reassign positions and colors
            let index = 0;
            this.buckets .forEach ( (bucket) => {
                bucket .forEach (([position, indexOriginal]) => {
                    template.position.copy(position);
                    template.updateMatrix();
                    this.mesh.setMatrixAt(index, template.matrix);

                    this.instanceColors[4*index + 0] = this.instanceColorsOriginal[4*indexOriginal + 0];
                    this.instanceColors[4*index + 1] = this.instanceColorsOriginal[4*indexOriginal + 1];
                    this.instanceColors[4*index + 2] = this.instanceColorsOriginal[4*indexOriginal + 2];
                    this.instanceColors[4*index + 3] = this.instanceColorsOriginal[4*indexOriginal + 3];

                    index += 1;
                });
            });

            this.mesh.instanceMatrix.needsUpdate = true;
            this.mesh.geometry.setAttribute('instanceColor', new THREE.InstancedBufferAttribute(this.instanceColors, 4));

            this.renderer.render(this.scene, this.camera);
        }
    }

    meshCreate() {
        let {Value: array, Shape: shape} = this.props.data;
        let totalCount = shape[0] * shape[1] * shape[2];

        let {ValueReferences: references, ValueReferencesEncodedInsert: inserts} = this.props.data;

        if (references) {
            for (let reference in inserts) {
                // Base64 decode
                let binary = atob(inserts[reference]);

                // Probably better to just flatten the index on each drawing pass rather than reshape here.
                // The implementation complexity of this is low so keeping for now.
                let index = 0;
                let array = [...new Uint8Array(shape[1])] .map (() =>
                                [...new Uint8Array(shape[2])].map(() =>
                                    [...new Uint8Array(shape[3])].map(() => binary.charCodeAt(index++))
                                )
                            );

                this.valueReferences[reference] = array;
            }

            array = references .map ((reference) => this.valueReferences[reference]);
        }

        let format = 0;
        if (shape.length === 4) {
            format = shape[3];
        }

        this.positionsIndices = [];
        this.buckets = [...new Array(totalCount + 1)] .map (() => []);
        this.instanceColorsOriginal = new Float32Array(4*totalCount);
        this.instanceColors = new Float32Array(4*totalCount);

        let scale = 100;
        let max = Math.max(...shape);
        let rescale = scale / max;
        let mean0 = rescale * shape[0] / 2;
        let mean1 = rescale * shape[1] / 2;
        let mean2 = rescale * shape[2] / 2;

        this.scene.remove(this.mesh);
        this.mesh = new THREE.InstancedMesh(this.geometry, this.material, totalCount);
        this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

        let template = new THREE.Object3D();
        let index = 0;

        let k = scale / max;
        array .forEach ( (axis1, index0) =>  {
            axis1 .forEach ( (axis2, index1) => {
                axis2 .forEach ( (value, index2) => {
                    let position = new THREE.Vector3(-(k*index0 + k*0.5 - mean0),
                                                     -(k*index1 + k*0.5 - mean1),
                                                     -(k*index2 + k*0.5 - mean2))

                    template.position.copy(position);
                    template.updateMatrix();
                    this.mesh.setMatrixAt(index, template.matrix);
                    this.positionsIndices.push([position, index, 0]);

                    if (format === 0) {
                        this.instanceColorsOriginal[4*index + 0] = 0.55;
                        this.instanceColorsOriginal[4*index + 1] = 0.55;
                        this.instanceColorsOriginal[4*index + 2] = 0.55;
                        this.instanceColorsOriginal[4*index + 3] = value / 255.0;
                    } else if (format === 3) {
                        this.instanceColorsOriginal[4*index + 0] = value[0] / 255.0;
                        this.instanceColorsOriginal[4*index + 1] = value[1] / 255.0;
                        this.instanceColorsOriginal[4*index + 2] = value[2] / 255.0;
                        this.instanceColorsOriginal[4*index + 3] = 0.8;
                    } else if (format === 4) {
                        this.instanceColorsOriginal[4*index + 0] = value[0] / 255.0;
                        this.instanceColorsOriginal[4*index + 1] = value[1] / 255.0;
                        this.instanceColorsOriginal[4*index + 2] = value[2] / 255.0;
                        this.instanceColorsOriginal[4*index + 3] = value[3] / 255.0;
                    }

                    index += 1;
                } )
            } )
        } );

        this.geometry.setAttribute('instanceColor', new THREE.InstancedBufferAttribute(new Float32Array(this.instanceColorsOriginal), 4));

        this.scene.add(this.mesh);
        this.renderer.render(this.scene, this.camera);
    };

    render() {
        if (this.mesh !== null) {
            this.meshCreate();
            this.previousCameraPosition = new THREE.Vector3();
            this.animate();
        }

        return <div id={this.domId} style={{width: 340, height: 340}}></div>
    }
}

function clipboardCopy(text, event) {
    let element = document.getElementById('clipboard-input');
    element.style.visibility = 'visible';
    element.value = text;
    element.select();
    element.setSelectionRange(0, 99999);
    document.execCommand("copy");
    element.blur();
    element.style.visibility = 'hidden';

    event.target.classList.add('clipboard-clicked');
}

let globalState = null;
globalState = {
    images: [],
    selectedImage: null,
    inspectionBoxes: [],
    onClick: (event, object) => {
        let {left, top, width, height, bottom, right} = event.target.getBoundingClientRect();
        let imageContainer = event.target.parentNode.parentNode;

        globalState.selectedImage && globalState.selectedImage.classList.remove('selected');

        let popup = <div className="inspection-box"
                         style={{top: top, left: right + 4}} />;

        ReactDOM.render(popup, document.getElementById('inspection-parent'));

        globalState.inspectionBoxes = [{left, top, width, height, bottom, right}];

        if (globalState.selectedImage === imageContainer) {
            globalState.selectedImage = null;
            ReactDOM.render(<div />, document.getElementById('inspection-parent'));
        } else {
            imageContainer.classList.add('selected');
            globalState.selectedImage = imageContainer;
        }

        globalState.onMouseMove(event, object);
    },
    onMouseMove: (event, object) => {
        /* bottom: 499
           height: 448
           left: 281
           right: 761
           top: 51
           width: 480
           x: 281
           y: 51 */

        if (globalState.selectedImage !== event.target.parentNode.parentNode) {
            return ;
        }

        let {left, top, right, bottom, width, height} = event.target.getBoundingClientRect();
        let px = (event.clientX - left) / width;
        let py = (event.clientY - top) / height;
        let x = event.clientX - left;
        let y = event.clientY - top;

        let {right: boxRight, top: boxTop} = globalState.inspectionBoxes[0];
        let popup = <ZoomBox data={object}
                             mainComponentBoundingBox={{left, top, right, bottom, width, height}}
                             zoomPosition={{px, py, x, y}}
                             zoomLevel={7} />;

        ReactDOM.render(popup, document.getElementById('inspection-parent'));
    }
};

class ZoomBox extends React.Component {
    render() {
        let { Value: value, Shape: shape, DisplayScale: displayScale } = this.props.data;
        let zoomLevel = this.props.zoomLevel;

        let {top: topMain, right: rightMain, bottom, left, width, height} = this.props.mainComponentBoundingBox;
        let {px, py, x, y} = this.props.zoomPosition;

        let top = 0;
        let right = 0;

        [top, bottom, left, right] = [
            top + height*(py - 0.1),
            top + height*(py + 0.1),
            left + width*(px - 0.1),
            left + width*(px + 0.1)
        ];

        let pixelRadius = 15;

        [top, bottom, left, right] = [
            y - pixelRadius,
            y + pixelRadius,
            x - pixelRadius,
            x + pixelRadius
        ];

        [top, bottom, left, right] = [top, bottom, left, right] .map ((n) => zoomLevel*n)

        /* rect(top, right, bottom, left) */
        return <div className="inspection-box" style={{
                clip: `rect(${top}px, ${right}px, ${bottom}px, ${left}px)`,
                top: topMain - top,
                left: rightMain - left + 4}}>
            <img src={value} className="image-zoom"
                 height={zoomLevel*displayScale*shape[0]} width={zoomLevel*displayScale*shape[1]} />
        </div>;
    }
}

function setDisplay(data) {
    [...data['Value']] .forEach ((element) => {
        if (element['Type'] === 'ApplicationSettings') {
            for (let setting in element['Value']) {
                if (setting === 'Title') {
                    document.title = element['Value'][setting];
                } else if (setting === 'Thumbnail') {
                    let link = document.querySelector('head link');
                    link.setAttribute('href', element['Value'][setting]['Value']);
                } else if (setting === 'Background') {
                    document.body.style.background = element['Value'][setting];
                }
            }
        }
    });

    ReactDOM.render(<DataDisplay data={data} globalState={globalState}/>, document.getElementById('data-display-container'));
}

var currentFrameIndex = 0;
function download(resourceType, event) {
    console.log('resourceType', resourceType);
    /*if (currentFrameIndex === 0) {
        return ;
    }*/

    let body = document.body;
    let element = event.target;
    element.classList.add("download-in-progress");
    body.classList.add("download-in-progress");
    element.disabled = true;

    query({
        "Request": "ResourceURL",
        "ResourceType": resourceType,
        "Game": lastSelectedGame,
        "ClientId": clientId
    }, function(fileUrl) {
        function onFileExists() {
            window.location = fileUrl;
            element.classList.remove("download-in-progress");
            body.classList.remove("download-in-progress");
            element.disabled = false;
        }

        let intervalId = setInterval(function() {
            fetch(fileUrl)
            .then(function() {
                clearInterval(intervalId);
                onFileExists();
            })
        }, 350);
    });
}

function initialize() {
    query({
        "Request": "Initial",
        "ClientId": clientId
    }, ({Data: data}) => {
        setDisplay(data);
    });
}

function query(request, process) {
    fetch('.', {
        method: 'POST',
        body: JSON.stringify(request)
    })
    .then((response) => response.json())
    .then(process);
}

initialize();