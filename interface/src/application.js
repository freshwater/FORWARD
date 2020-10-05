
"🎲 ⚀ ⚁ ⚂ ⚃ ⚄ ⚅";

let clientId = new String(Math.random()).substring(2);

document.body.style.background = 'black';

class GameSelection extends React.Component {
    render() {
        return <select defaultValue={this.props.selectedGame}
                        onChange={(event) => {reset(event.target.value)}}> {
                this.props.gamesList .map (
                    (gameTitle) => <option value={gameTitle} key={gameTitle}>{gameTitle}</option>
                ) }
        </select>;
    }
}

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

function query(request, process) {
    fetch('.', {
        method: 'POST',
        body: JSON.stringify(request)
    })
    .then(function(response) { return response.json(); })
    .then(process);
}

query({'Request': 'AvailableGames', 'ClientId': clientId}, function(response) {
    let games = response['AvailableGames'];
    ReactDOM.render(<GameSelection gamesList={games} selectedGame={"SuperMarioBros-Nes"}/>, document.querySelector('.title'));
});

let downloadId = new String(Math.random()).substring(2);
ReactDOM.render([<DownloadsSelection id={downloadId} values={[".mp4 Replay Video", ".bk2 Replay Data", ".json Action Sequence"]}
                                        initialValue=".mp4 Replay Video" />,
                    <span>&nbsp;</span>,
                    <button onClick={(event) => download(document.getElementById(downloadId).value, event)}>Download</button>],
                document.querySelector('.downloads-selection'));

class DataDisplay extends React.Component {
    render() {
        let {Type: type, Value: value, ...object} = this.props.data;

        if (type === "List") {
            return <div className="list">
                {value .map ((element, index) => <DataDisplay data={element} index={index} />)}
            </div>;

        } else if (type === "Dictionary") {
            return <table className="dictionary">
                <tbody>
                    {value .map (([key1, value1]) => <tr>
                        <td className="key"><DataDisplay data={key1} /></td>
                        <td className="value"><DataDisplay data={value1} /></td>
                    </tr>)}
                </tbody>
            </table>;

        } else if (type === "Image") {
            let {Shape: shape, DisplayScale: displayScale, Elements: elements} = object;

            return <div key={this.props.index} style={{position: 'relative', display: 'inline-block'}}>
                <div className="image">
                    <img src={value} className="image" style={{imageRendering: 'pixelated'}} height={displayScale*shape[0]} width={displayScale*shape[1]} />
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
                    setDisplay(response['Data']);
                })
            };

            /*let buttonIds = value .flatMap (({Type: type, Id: id}) => type === 'Button' ? [id] : [])

            setTimeout(function() {
                let buttons = buttonIds .map ((id) => document.getElementById(id));
                let maxWidth = Math.max(...[...buttons].map(button => button.clientWidth));
                let maxHeight = Math.max(...[...buttons].map(button => button.clientHeight));
                [...buttons].forEach(button => button.style.width = `${maxWidth}px`);
                [...buttons].forEach(button => button.style.height = `${maxHeight + 5}px`);
            }, 10)*/

            return <button id={id} key={id} className="button" onClick={onClick}>{value}</button>

        } else {
            return <div></div>;
        }
    }
}

import * as THREE from './three/three.min.js';
import { OrbitControls } from './three/OrbitControls.js';
import { LightProbeGenerator } from './three/LightProbeGenerator.js';

class ArrayPlot3D extends React.Component {
    constructor() {
        super();
        this.domId = `${Math.random()}`;
    }

    componentDidMount() {
        let {Value: array, Shape: shape} = this.props.data;
        let totalCount = shape[0] * shape[1] * shape[2];

        let camera, scene, renderer, cubeCamera;
        let mesh = null;
        let positionsIndices = [];
        let instanceColorsOriginal = new Float32Array(4*totalCount);
        let instanceColors = new Float32Array(4*totalCount);
        let previousCameraPosition = new THREE.Vector3(0, 0, 0);

        let domElement = document.getElementById(this.domId);

        initialize(array);
        animate();

        function initialize(array) {
            scene = new THREE.Scene();

            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(domElement.clientWidth, domElement.clientHeight);
            domElement.appendChild(renderer.domElement);

            let cubeRenderTarget = new THREE.WebGLCubeRenderTarget( 256, {
                // encoding: THREE.sRGBEncoding,
                format: THREE.RGBAFormat
            } );

            cubeCamera = new THREE.CubeCamera( 1, 1000, cubeRenderTarget );

            let lightProbe = new THREE.LightProbe();
            scene.add(lightProbe);

            let urls = ['px', 'nx', 'py', 'ny', 'pz', 'nz'] .map (direction => `three/textures/${direction}.png`)

            new THREE.CubeTextureLoader().load(urls, function (cubeTexture) {
                // cubeTexture.encoding = THREE.sRGBEncoding;
                scene.background = cubeTexture;
                cubeCamera.update(renderer, scene);

                lightProbe.copy(LightProbeGenerator.fromCubeRenderTarget(renderer, cubeRenderTarget));
                scene.background = new THREE.Color(0xffffff);

                let scale = 100;

                let max = Math.max(...shape);
                let rescale = scale / max;
                let mean0 = rescale * shape[0] / 2;
                let mean1 = rescale * shape[1] / 2;
                let mean2 = rescale * shape[2] / 2;

                let t0 = performance.now()

                let material = new THREE.MeshStandardMaterial({
                    color: 0xffffff,
                    metalness: 0,
                    roughness: 0,
                    envMap: cubeTexture,
                    envMapIntensity: 1,
                    transparent: true,
                });

                let k = scale / max;
                let geometry = new THREE.BoxBufferGeometry(k, k, k);

                mesh = new THREE.InstancedMesh(geometry, material, totalCount);
                mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

                let template = new THREE.Object3D();
                let index = 0;

                array .forEach ( (axis1, index0) =>  {
                    axis1 .forEach ( (axis2, index1) => {
                        axis2 .forEach ( (value, index2) => {
                            template.position.set(k*index0 + k*0.5 - mean0,
                                                  k*index1 + k*0.5 - mean1,
                                                  k*index2 + k*0.5 - mean2);

                            template.updateMatrix();

                            mesh.setMatrixAt(index, template.matrix);

                            positionsIndices.push([
                                /* position */ new THREE.Vector3(k*index0 + k*0.5 - mean0, k*index1 + k*0.5 - mean1, k*index2 + k*0.5 - mean2),
                                /* indexOriginal */ index
                            ])

                            instanceColorsOriginal[4*index + 0] = 0.6;
                            instanceColorsOriginal[4*index + 1] = 0.6;
                            instanceColorsOriginal[4*index + 2] = 0.6;
                            instanceColorsOriginal[4*index + 3] = value;

                            index += 1;
                        } )
                    } )
                } );

                geometry.setAttribute('instanceColor', new THREE.InstancedBufferAttribute(new Float32Array(instanceColorsOriginal), 4));

                material.onBeforeCompile = function ( shader ) {
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

                scene.add(mesh);

                renderer.render(scene, camera);
                console.log('a.', performance.now() - t0)
            });

            camera = new THREE.PerspectiveCamera(70, domElement.clientWidth / domElement.clientHeight, 1, 10000);
            camera.position.x = 120;
            camera.position.y = 120;
            camera.position.z = 120;

            let controls = new OrbitControls(camera, renderer.domElement);
            controls.minDistance = 80;
            controls.maxDistance = 340;

            domElement.addEventListener('resize', onWindowResize, false);
        }

        function onWindowResize() {
            camera.aspect = domElement.clientWidth / domElement.clientHeight;
            camera.updateProjectionMatrix();

            renderer.setSize(domElement.clientWidth, domElement.clientHeight);
        }

        function animate() {
            requestAnimationFrame(animate);

            if (mesh === null) {
                return ;
            }

            // Couldn't figure out a depth/blend setting to automatically set
            // the render order as back-to-front from any direction.
            // This will work for now.
            if (!camera.position.equals(previousCameraPosition) && Math.random() < 1) {
                previousCameraPosition.copy(camera.position);

                let template = new THREE.Object3D();

                positionsIndices.sort(([a], [b]) => {
                    return camera.position.distanceTo(a) <= camera.position.distanceTo(b) ? 1 : -1;
                });

                let index = 0;
                for (let [position, indexOriginal] of positionsIndices) {
                    template.position.copy(position);

                    template.updateMatrix();

                    mesh.setMatrixAt(index, template.matrix);

                    instanceColors[4*index + 0] = instanceColorsOriginal[4*indexOriginal + 0];
                    instanceColors[4*index + 1] = instanceColorsOriginal[4*indexOriginal + 1];
                    instanceColors[4*index + 2] = instanceColorsOriginal[4*indexOriginal + 2];
                    instanceColors[4*index + 3] = instanceColorsOriginal[4*indexOriginal + 3];

                    index += 1;
                }

                mesh.instanceMatrix.needsUpdate = true;
                mesh.geometry.setAttribute('instanceColor', new THREE.InstancedBufferAttribute(instanceColors, 4));

                renderer.render(scene, camera);
            }
        }
    }

    render() {
        return <div id={this.domId} style={{background: 'red', width: 340, height: 340}}></div>
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

function setDisplay(data) {
    let dataDisplay = ReactDOM.render(<DataDisplay data={data}/>, document.getElementById('data-display-container'));
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

let lastSelectedGame = null;
function reset(game=lastSelectedGame) {
    lastSelectedGame = game;
    document.title = game;

    query({
        "Request": "Reset",
        "Game": game,
        "ClientId": clientId
    }, function(response) {
        let {Observation: obs,
                BlockEncodings: encodings,
                Blocks: blocks,
                FrameIndex: frameIndex} = response;

        currentFrameIndex = frameIndex;

        query({
            "Request": "ImageUrl",
            "ClientId": clientId
        }, function(faviconUrl) {
            let link = document.querySelector('head link');
            link.setAttribute('href', faviconUrl);
        });

        /* */
        let {Data: data} = response;
        setDisplay(data);
    });
}

reset("SuperMarioBros-Nes");