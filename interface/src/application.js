
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

import { ArrayPlot3D } from './ArrayPlot3D.js';

class DataDisplay extends React.Component {
    render() {
        let {Type: type, Value: value, ...object} = this.props.data;
        let globalState = this.props.globalState;

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
                                     onMouseMove={(event) => this.props.globalState.onMouseMove(event, {Value: value, ...object})}
                                     onMouseLeave={(event) => this.props.globalState.onMouseLeave(event)} />
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
                {value .map ((row, i) => <tr key={i}>{row .map ((elem, j) => <td key={j}>{elem}</td> )}</tr>)}
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
            let {/*Label: label,*/ Id: id, Minimum: min, Maximum: max, Value: value} = this.props.data;
            let onChange = function (event) {
                let newValue = event.target.value;

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

let globalState_ = null;
globalState_ = {
    images: [],
    selectedImage: null,
    inspectionData: {},
    onClick: (event, object) => {
        let {left, top, width, height, bottom, right} = event.target.getBoundingClientRect();
        let imageContainer = event.target.parentNode.parentNode;

        globalState_.selectedImage && globalState_.selectedImage.classList.remove('selected');

        let popup = <div className="inspection-box"
                         style={{top: top, left: right + 4}} />;

        ReactDOM.render(popup, document.getElementById('inspection-parent'));

        if (globalState_.selectedImage === imageContainer) {
            globalState_.selectedImage = null;
            ReactDOM.render(<div />, document.getElementById('inspection-parent'));
        } else {
            imageContainer.classList.add('selected');
            globalState_.selectedImage = imageContainer;
        }

        globalState_.onMouseMove(event, object);
    },
    onMouseMove: (event, object) => {
        let {InstanceId: instanceId} = object;

        if (globalState_.selectedImage !== event.target.parentNode.parentNode) {
            return ;
        }

        let {left, top, right, bottom, width, height} = event.target.getBoundingClientRect();
        let px = (event.clientX - left) / width;
        let py = (event.clientY - top) / height;
        let x = event.clientX - left;
        let y = event.clientY - top;

        let load = (inspectionData) => {
            let popup = <div>
                <ZoomBox data={object}
                        mainComponentBoundingBox={{left, top, right, bottom, width, height}}
                        zoomPosition={{x, y}}
                        zoomLevel={7} />
                <InspectionTableBox data={object}
                                    inspectionData={inspectionData}
                                    mainComponentBoundingBox={{left, top, right, bottom, width, height}}
                                    zoomPosition={{x, y}}
                                    zoomLevel={2} />
            </div>;

            ReactDOM.render(popup, document.getElementById('inspection-parent'));
            document.getElementById('inspection-parent').style.visibility = 'visible';
        };

        if (instanceId in globalState_.inspectionData) {
            if (globalState_.inspectionData[instanceId] !== "InFlight") {
                load(globalState_.inspectionData[instanceId]);
            }
        } else {
            globalState_.inspectionData[instanceId] = "InFlight";
            query({
                "Request": "Inspection",
                "ClientId": clientId,
                "InstanceId": instanceId
            }, ({Value: value}) => {
                globalState_.inspectionData[instanceId] = value;
                load(value);
            });
        }
    },
    onMouseLeave: (event) => {
        if (globalState_.selectedImage === event.target.parentNode.parentNode) {
            document.getElementById('inspection-parent').style.visibility = 'hidden';
        }
    }
};

class ZoomBox extends React.Component {
    render() {
        let { Value: value, Shape: shape, DisplayScale: displayScale } = this.props.data;
        let zoomLevel = this.props.zoomLevel;

        let {top: topMain, right: rightMain} = this.props.mainComponentBoundingBox;
        let {x, y} = this.props.zoomPosition;

        let pixelRadius = 15;

        let [top, bottom, left, right] = [
            y - pixelRadius,
            y + pixelRadius,
            x - pixelRadius,
            x + pixelRadius
        ] .map (_ => _*zoomLevel);

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

class InspectionTableBox extends React.Component {
    render() {
        let { Shape: shape, DisplayScale: displayScale } = this.props.data;
        let inspectionData = this.props.inspectionData;

        let zoomLevel = this.props.zoomLevel;

        let {top: topMain, right: rightMain} = this.props.mainComponentBoundingBox;
        let {x, y} = this.props.zoomPosition;

        let pixelRadius = 15;

        let [top, bottom, left, right] = [
            y - pixelRadius,
            y + pixelRadius,
            x - pixelRadius,
            x + pixelRadius
        ];

        let [dataHeight, dataWidth, dataChannels = 0] = shape;

        let dataRowStart = top / displayScale;
        let dataRowStop = bottom / displayScale;
        let dataColumnStart = left / displayScale;
        let dataColumnStop = right / displayScale;

        // Need stable span as user moves mouse around.
        dataRowStop = Math.round(dataRowStart) + Math.ceil(dataRowStop - dataRowStart);
        dataRowStart = Math.round(dataRowStart);
        dataColumnStop = Math.round(dataColumnStart) + Math.ceil(dataColumnStop - dataColumnStart);
        dataColumnStart = Math.round(dataColumnStart);

        let slice = [...new Uint8Array(dataRowStop - dataRowStart)] .map ((_, row) =>
                        [...new Uint8Array(dataColumnStop - dataColumnStart)].map((_, column) => {
                            let rowIndex = dataRowStart + row;
                            let columnIndex = dataColumnStart + column;

                            if (0 < rowIndex && rowIndex < dataHeight &&
                                0 < columnIndex && columnIndex < dataWidth) {
                                return inspectionData[dataRowStart + row][dataColumnStart + column];
                            } else {
                                return dataChannels === 0 ? <span>&nbsp;&nbsp;&nbsp;</span>
                                                          : [...new Uint8Array(dataChannels)] .map (() => <span>&nbsp;&nbsp;&nbsp;</span>);
                            }
                        })
                    );

        let keyMake = (a, b, c) => `(${a},${b},${c})`;
        return <div className="inspection-table-box" channel-count={dataChannels} style={{
                        top: topMain + 200 + 10,
                        left: rightMain + 4}}>
            <table>
                <tbody>
                    {slice .map (
                        (row, rowIndex) => <tr key={rowIndex}>
                            {row .map ((value, columnIndex) =>
                                <React.Fragment key={keyMake(rowIndex, columnIndex, 0)}><td key={keyMake(rowIndex, columnIndex, 1)} className="left"></td>{
                                    dataChannels === 0 ? <td key={keyMake(rowIndex, columnIndex, 2)}>{value}</td>
                                                       : value .map ((v, i) => <td key={keyMake(rowIndex, columnIndex, 2 + i)} className={`i${i}`}>{v}</td>)}
                                <td key={keyMake(rowIndex, columnIndex, -1)} className="right"></td></React.Fragment>
                            )}
                        </tr>)}
                </tbody>
            </table>
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

    ReactDOM.render(<DataDisplay data={data} globalState={globalState_}/>, document.getElementById('data-display-container'));
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