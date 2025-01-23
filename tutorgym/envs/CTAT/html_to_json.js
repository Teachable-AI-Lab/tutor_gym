
async function getNextHtml() {
    try {
        const response = await fetch('http://localhost:3000/get_next_html',
            { 
            method: 'GET',
            headers: {
                'Accept': 'text/plain',
                crossdomain : true,
                }
            }
        );
        const data = await response.text();
        console.log('Success:', data);
        return data
    } catch (error) {
        console.error('Error:', error);
    }

}

async function saveHtmlJson() {
    try {
        const response = await fetch('http://localhost:3000/save_html_json',
        {
            method: 'POST',
            headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            // crossdomain : true,
            },
            body : JSON.stringify({a: 1, b: 'Textual content'})
        });
        const data = await response.text();
        console.log('Success:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function saveHtmlImage(imageData) {
    try {
        const response = await fetch('http://localhost:3000/save_html_image',
        {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                // crossdomain : true,
            },
            body: JSON.stringify({
                image: imageData
            })
        });
        const data = await response.text();
        console.log('Success:', data);
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // Create a new iframe
    const iframe = document.getElementById('tutor_iframe');
        
    // Wait for iframe to load
    iframe.onload = () => {
        let iframeDocument;
        try {
            iframeDocument = iframe.contentDocument || iframe.contentWindow.document;
            // Work with iframe DOM here
        } catch (e) {
            console.error('Cannot access iframe DOM - possible cross-origin restriction:', e);
        }

        console.log("IFRAME LOADED")
        Tutor_DOM_to_JSON(iframeDocument)
    };

    next_html = await getNextHtml();
    iframe.src = next_html;
    
    // Now you can work with the iframe's DOM
    // For example:
    // iframeDocument.body.innerHTML = '<div>Hello from iframe!</div>';

    
    // Error handling
    iframe.onerror = (error) => {
        console.error('Error loading iframe:', error);
    };
});


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

function getRealChildrenBounds(elem) {
    // Get all children including the parent
    // const elements = [parentElement, ...parentElement.getElementsByTagName('*')];
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

function _recurse_handle_elem(elem, infos){
    // if(elem?.gym_covered){
    //    return
    // }
    // elem.gym_covered = true



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
    console.log(elem, info)
}

function Tutor_DOM_to_JSON(tutor_dom){
    // Get bounding box if element is rendered

    infos = []
    _recurse_handle_elem(tutor_dom.body, infos)
    let body_bounds = getRealChildrenBounds(tutor_dom.body)


    html2canvas(tutor_dom.body).then(
        (canvas) => {
            // canvas.width = body_bounds.width
            // canvas.height = body_bounds.height



            
            const imageData = canvas.toDataURL('image/png');
            console.log(imageData)
            // // Remove the data URL prefix to get just the base64 data
            // const base64Data = imageData.replace(/^data:image\/png;base64,/, '');
            saveHtmlImage(imageData)
            
            // document.body.appendChild(canvas);
    });


    // for (const info of infos) {
    //     console.log(info)
    // }

    // return result;
}
