const recognitionLimit = 5 * 1024 * 1024

export function recognitionImage(file) {
  if (file.size > recognitionLimit) return Promise.reject(new Error('请选择不超过 5 MB 的图片'))
  return new Promise((resolve, reject) => {
    wx.getFileSystemManager().readFile({
      filePath: file.path,
      encoding: 'base64',
      success({ data }) {
        let format
        if (data.startsWith('/9j/')) format = 'jpeg'
        else if (data.startsWith('iVBORw0KGgo')) format = 'png'
        else if (data.startsWith('UklGR') && wx.base64ToArrayBuffer) {
          const prefix = new Uint8Array(wx.base64ToArrayBuffer(data.slice(0, 16)))
          if (String.fromCharCode(...prefix.slice(8, 12)) === 'WEBP') format = 'webp'
        }
        if (!format) {
          reject(new Error('图片识别支持 JPG、PNG 和 WebP'))
          return
        }
        resolve(`data:image/${format};base64,${data}`)
      },
      fail: () => reject(new Error('无法读取选中的图片，请重新选择')),
    })
  })
}

let imageSequence = 0

export function previewFile(imageUrl) {
  const data = /^data:image\/(jpeg|png|gif|webp);base64,([A-Za-z0-9+/=]+)$/i.exec(imageUrl || '')
  if (!data) return Promise.resolve('')
  const filePath = `${wx.env.USER_DATA_PATH}/question-${Date.now()}-${++imageSequence}.${data[1]}`
  return new Promise((resolve, reject) => {
    wx.getFileSystemManager().writeFile({
      filePath,
      data: data[2],
      encoding: 'base64',
      success: () => resolve(filePath),
      fail: () => reject(new Error('无法打开题图，请重试')),
    })
  })
}

export function removePreview(filePath) {
  if (filePath) wx.getFileSystemManager().unlink({ filePath })
}
