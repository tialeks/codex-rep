import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count == 3 else { fatalError("usage: mask input.png mask.png") }
guard !FileManager.default.fileExists(atPath: args[2]) else { fatalError("Preserve previous attempts: mask output already exists") }
let handler = VNImageRequestHandler(url: URL(fileURLWithPath: args[1]), options: [:])
let request = VNGenerateForegroundInstanceMaskRequest()
try handler.perform([request])
guard let result = request.results?.first, !result.allInstances.isEmpty else { fatalError("No foreground found") }
let buffer = try result.generateScaledMaskForImage(forInstances: result.allInstances, from: handler)
let image = CIImage(cvPixelBuffer: buffer)
let context = CIContext()
guard let cg = context.createCGImage(image, from: image.extent, format: .L8, colorSpace: CGColorSpaceCreateDeviceGray()),
      let dest = CGImageDestinationCreateWithURL(URL(fileURLWithPath: args[2]) as CFURL, UTType.png.identifier as CFString, 1, nil) else { fatalError("Cannot write mask") }
CGImageDestinationAddImage(dest, cg, nil)
guard CGImageDestinationFinalize(dest) else { fatalError("Mask write failed") }
print("instances=\(result.allInstances.count) width=\(cg.width) height=\(cg.height)")
