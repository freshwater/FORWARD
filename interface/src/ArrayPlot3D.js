
import * as THREE from './three/three.min.js';
import { OrbitControls } from './three/OrbitControls.js';
import { LightProbeGenerator } from './three/LightProbeGenerator.js';

export class ArrayPlot3D extends React.Component {
    constructor() {
        super();
        this.domId = `${Math.random()}`;

        this.initialize = this.initialize.bind(this);
        this.animate = this.animate.bind(this);

        this.scene = new THREE.Scene();
        this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
        this.camera = null;
        this.previousCameraPosition = new THREE.Vector3(0, 0, 0);
        this.previousMousePosition = new THREE.Vector2(0, 0);
        this.mesh = null;
        this.lines = null;
        this.positionToIndices = () => {};
        this.lastKMouseOverCoordinates = [];
        this.mousePosition = new THREE.Vector2(1, 1);
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
        domElement.addEventListener('mousemove', onMouseMove, false);

        function onWindowResize() {
            this.camera.aspect = domElement.clientWidth / domElement.clientHeight;
            this.camera.updateProjectionMatrix();

            this.renderer.setSize(domElement.clientWidth, domElement.clientHeight);
        }

        let this1 = this;
        function onMouseMove(event) {
            event.preventDefault();

            this1.mousePosition.x = (event.offsetX / domElement.clientWidth)*2 - 1;
            this1.mousePosition.y = -(event.offsetY / domElement.clientHeight)*2 + 1.01;
        }
    }

    animate() {
        requestAnimationFrame(this.animate);

        if (this.mesh === null) {
            return ;
        }

        let shouldUpdate = false;

        // Couldn't figure out a depth/blend setting to automatically set
        // the render order as back-to-front from any direction.
        // This will work for now.
        if (!this.camera.position.equals(this.previousCameraPosition) && Math.random() < 1) {
            shouldUpdate = true;
            this.previousCameraPosition.copy(this.camera.position);

            let template = new THREE.Object3D();

            // let t0 = performance.now();

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
            // this.positionsIndices.push([position, index, 0, isEdgeBlock]);
            this.buckets .forEach ((_, index) => { this.buckets[index] = [] });
            let increment = 1 / this.positionsIndices.length;
            this.positionsIndices .forEach ((tuple) => {
                // ignore fully transparent blocks
                let [_position, indexOriginal, cameraDistance, isEdgeBlock] = tuple;
                if (isEdgeBlock || this.instanceColorsOriginal[4*indexOriginal + 3] !== 0) {
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
        }

        if (!this.mousePosition.equals(this.previousMousePosition)) {
            shouldUpdate = true;
            this.previousMousePosition.copy(this.mousePosition);

            let raycaster = new THREE.Raycaster();
            raycaster.setFromCamera(this.mousePosition, this.camera);
            let intersection = raycaster.intersectObject(this.mesh);

            if (intersection.length > 0) {
                let instanceId = intersection[0].instanceId;

                this.instanceColors[4*instanceId + 0] = 1;
                this.instanceColors[4*instanceId + 1] = 0;
                this.instanceColors[4*instanceId + 2] = 0;
                this.instanceColors[4*instanceId + 3] = 1;

                // let matrix = new THREE.Matrix4();
                // this.mesh.getMatrixAt(instanceId, matrix);
                // let index012 = this.positionToIndices(matrix.elements.slice(12, 12 + 3));
                this.lastKMouseOverCoordinates.push(intersection[0].point);
                if (this.lastKMouseOverCoordinates.length > 12) {
                    this.lastKMouseOverCoordinates = this.lastKMouseOverCoordinates.slice(1);
                }

                let [dX, dY, dZ] = [0, 0, 0];
                this.lastKMouseOverCoordinates.slice(1) .forEach ((_, index) => {
                    let {x: x2, y: y2, z: z2} = this.lastKMouseOverCoordinates[index + 1];
                    let {x: x1, y: y1, z: z1} = this.lastKMouseOverCoordinates[index];

                    [dX, dY, dZ] = [
                        dX + x2 - x1,
                        dY + y2 - y1,
                        dZ + z2 - z1
                    ];
                });

                let length = this.lastKMouseOverCoordinates.length - 1;
                [dX, dY, dZ] = [dX, dY, dZ] .map (_ => parseInt(`${Math.sign(Math.round(_ / length))}`, 10));

                console.log(dX, dY, dZ);
            }
        }

        if (shouldUpdate) {
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
        this.scene.remove(this.lines);
        this.mesh = new THREE.InstancedMesh(this.geometry, this.material, totalCount);
        this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);

        let template = new THREE.Object3D();
        let index = 0;

        this.positionToIndices = ([x, y, z]) => {
            return [
                Math.round((-x + mean0 - k*0.5) / k),
                Math.round((-y + mean1 - k*0.5) / k),
                Math.round((-z + mean2 - k*0.5) / k),
            ];
        };

        let k = scale / max;
        array .forEach ( (axis1, index0) =>  {
            axis1 .forEach ( (axis2, index1) => {
                axis2 .forEach ( (value, index2) => {
                    let position = new THREE.Vector3(-(k*index0 + k*0.5 - mean0),
                                                     -(k*index1 + k*0.5 - mean1),
                                                     -(k*index2 + k*0.5 - mean2))

                    // Used to keep transparent edge blocks for mouse cursor intersection
                    // that would otherwise be removed.
                    // A better method will be to just use one large cube for the
                    // intersection and use the point to determine the underlying block.
                    let isEdgeBlock = (index0 === 0 || index1 === 0 || index2 === 0
                                       || index0 === shape[0] - 1
                                       || index1 === shape[1] - 1
                                       || index2 === shape[2] - 1);

                    template.position.copy(position);
                    template.updateMatrix();
                    this.mesh.setMatrixAt(index, template.matrix);
                    this.positionsIndices.push([position, index, 0, isEdgeBlock]);

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

        // EulerianGraphQ@PetersonGraph[4, 1] False
        let ps = [
            [0, 0, 0],
            [0, 0, 1],
            [0, 1, 1],
            [0, 1, 0],

            [0, 0, 0],
            [1, 0, 0],
            [1, 0, 1], [0, 0, 1], [1, 0, 1],
            [1, 1, 1], [0, 1, 1], [1, 1, 1],
            [1, 1, 0], [0, 1, 0], [1, 1, 0],
            [1, 0, 0]
        ];

        let [h, w, d] = shape;
        let corners = ps .map(([i, j, k]) => [h*i, w*j, d*k]);

        corners = corners .map ( ([x, y, z]) => {
            return new THREE.Vector3(-(k*x - mean0),
                                     -(k*y - mean1),
                                     -(k*z - mean2));
        });

        let material = new THREE.LineBasicMaterial({
            color: 0x00b0b0,
        });

        let geometry = new THREE.BufferGeometry().setFromPoints(corners);
        this.lines = new THREE.Line(geometry, material);

        this.scene.add(this.lines);

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