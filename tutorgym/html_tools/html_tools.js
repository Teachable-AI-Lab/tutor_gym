
// const urlParams = new URLSearchParams(window.location.search);
const host_url = window.location.origin

// -------------------------------------------
// : REST Endpoints w/ host server 

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    crossdomain : true,
}

function connectToHost(process_htmls) {
    return new Promise((resolve, reject) => {

        const socket = io(host_url, {
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
        }); 

        socket.on('connect', () => {
            console.log('Connected to host', host_url);
            resolve(socket);
        });

        socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            reject(error);
        });

        socket.on("send_html_configs", async (data, callback) =>{
            console.log("Acquired HTML CONFIGS", data)

            try{
                await process_htmls(data['html_configs'])    
                callback({"success" : true})
            }catch (error){
                console.error('Error:', error);
                callback({"error" : jsonify(error)})
            }
            
            console.log("AFT FINISHED")
            
        })

        // Optional: Add timeout
        setTimeout(() => {
            if (!socket.connected) {
                reject(new Error('Connection timeout'));
            }
        }, 5000);
    })
}

// async function getHtmlConfigs() {
//     try {
//         const response = await fetch(host_url + '/get_html_configs',
//         {
//             method: 'GET',
//             headers: HEADERS
//         });
//         const data = await response.text();
//         console.log('Success:', data);
//         return JSON.parse(data)
//     } catch (error) {
//         console.error('Error:', error);
//     }
// }

async function saveHtmlJson(html_json, filepath) {
    try {
        const response = await fetch(host_url + '/save_html_json',
        {
            method: 'POST',
            headers: HEADERS,
            body : JSON.stringify({html_json, filepath})
        });
        const data = await response.text();
        console.log('Success:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function saveHtmlImage(image_data, filepath) {
    try {
        const response = await fetch(host_url + '/save_html_image',
        {
            method: 'POST',
            headers: HEADERS,
            body: JSON.stringify({image_data, filepath})
        });
        const data = await response.text();
        console.log('Success:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function processingFinished() {
    try {
        const response = await fetch(host_url + '/processing_finished',
        { 
            method: 'POST',
            headers: HEADERS
        });
        const data = await response.text();
        console.log('Success:', data);
        return JSON.parse(data)
    } catch (error) {
        console.error('Error:', error);
    }
}

// ----------------------------------------------------
// Main Processing Loop

function get_iframe_doc(iframe){
    try {
        return iframe.contentDocument || iframe.contentWindow.document;
        // Work with iframe DOM here
    } catch (e) {
        console.error('Cannot access iframe DOM - possible cross-origin restriction:', e);
    }
    return null
}

document.addEventListener('DOMContentLoaded', async () => {
    // Create a new iframe
    const iframe = document.getElementById('tutor_iframe');
    // Wait for iframe to load
    
    let process_htmls = async (html_configs) =>{
        // Set the source in the iframe to each HTML file one at a time
        for(let config of html_configs){
            let html_path = config.html_path
            console.log("BEF1")
            console.log("html_config", config)


            console.log("BEF")
            // Promise for when processing finished
            let proc_finished = new Promise((resolve, reject) => {
                // Set onload() for when src changes
                iframe.onload = async () => {
                    console.log("On Load")
                    let iframeDocument = get_iframe_doc(iframe)


                    // Do HTML -> JSON
                    if(config.get_json){
                        let json = Tutor_DOM_to_JSON(iframeDocument)
                        console.log("DOM TO JSON", json)
                        await saveHtmlJson(json, config.json_path)
                    }

                    // Do HTML -> Image
                    if(config.get_image){
                        let imageData = await Tutor_DOM_to_Image(iframeDocument)
                        console.log("DOM TO Image", imageData)
                        await saveHtmlImage(imageData, config.image_path)    
                    }
                    // Resolve proc_finished Promise
                    resolve(true)
                };
                iframe.onerror = (error) => {
                    console.error('Error loading iframe:', error);
                    reject()
                };
            });
            console.log("AFT")
            
            // Trigger onload by setting the source
            iframe.src = host_url + "/" + html_path;
            console.log("src", iframe.src)

            // Wait for the processing to finish before next loop 
            let val = await proc_finished;
            console.log("-- FINISHED -- ", val)
        }
    }

    socket = await connectToHost(process_htmls);
    
    // processingFinished()
});






// -------------------------------------------
// Tutor_DOM_to_JSON

function get_element_info(elem){
    // console.log("!", elem.id)
    let info = {
        id: elem.id || null,
        locked: !elem.isContentEditable,
    };
    if(elem?.tagName){
        info['tag'] = elem.tagName.toLowerCase()
    }
    if (elem.getBoundingClientRect) {
        let bbox = elem.getBoundingClientRect();
        info['x'] = bbox.x
        info['y'] = bbox.y
        info['width'] = bbox.width
        info['height'] = bbox.height
    }
    return info
}

function _recurse_handle_elem(elem, infos){
    let info = get_element_info(elem)
    
    children = elem?.children || []
    
    if(children.length > 0){
        child_ids = []
        for (let child of children) {
            child_ids.push(child.id)
            _recurse_handle_elem(child, infos)
        }
        info['child_ids'] = child_ids;
    }else if(elem?.innerHTML){
        info['value'] = elem?.innerHTML
    }
    
    infos.push(info)
    // console.log(elem, info)
}

async function Tutor_DOM_to_JSON(tutor_dom){
    infos = []
    _recurse_handle_elem(tutor_dom.body, infos)
    return JSON.stringify(infos);
}

// -------------------------------------------
// Tutor_DOM_to_Image

function getRealChildrenBounds(elem) {
    // Get surrounding bounding box of an element's children
    //  TODO: Maybe not useful

    const children = elem.children
    console.log(children)
    // Initialize min/max values
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;
    
    // Loop through all elements and find the extremes
    for(let child of children){ 
        if (child.getBoundingClientRect) {
            const bbox = child.getBoundingClientRect();
            minX = Math.min(minX, bbox.x);
            minY = Math.min(minY, bbox.y);
            maxX = Math.max(maxX, bbox.x + bbox.width);
            maxY = Math.max(maxY, bbox.y + bbox.height);
        }
    };
    
    // Return the total bounding box
    return {
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY,
        right: maxX,
        bottom: maxY
    };
}

async function Tutor_DOM_to_Image(tutor_dom){
    // TODO: Should I do something with this?
    // let body_bounds = getRealChildrenBounds(tutor_dom.body)

    return (
        html2canvas(tutor_dom.body).then(
        (canvas) => {
            // canvas.width = body_bounds.width
            // canvas.height = body_bounds.height
            
            const imageData = canvas.toDataURL('image/png');
            // console.log(imageData)
            // // Remove the data URL prefix to get just the base64 data
            // const base64Data = imageData.replace(/^data:image\/png;base64,/, '');
            return imageData
            
            // document.body.appendChild(canvas);
    }))
}

