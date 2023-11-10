#include "Struct/ShaderStructs.hlsli"
#include "ShaderFunctions.hlsli"

Texture2D vats : register(t11);

VertexToPixel main(VertexInput input)
{
    VertexToPixel result;
    float4x4 skinningMatrix =
    {
        	1, 0, 0, 0,
		0, 1, 0, 0,
		0, 0, 1, 0,
		0, 0, 0, 1
    };

    if (!OB_isStatic)
    {
        skinningMatrix = 0;
        skinningMatrix += input.BoneWeights.x * SB_BoneData[input.BoneIDs.x];
        skinningMatrix += input.BoneWeights.y * SB_BoneData[input.BoneIDs.y];
        skinningMatrix += input.BoneWeights.z * SB_BoneData[input.BoneIDs.z];
        skinningMatrix += input.BoneWeights.w * SB_BoneData[input.BoneIDs.w];
    }
    
    //First pixel 
    //
    //Red - Number of frames
    //
    //Green - Framerate 
    //
    //Blue 
    //
    //Alpha
    
    float4 vtxPos = input.Position;
    float3 vtxNorm = input.Normal;
    
    //Sample number of animation frames and framerate from first pixel
    uint numFrames = vats[float2(0, 0)].r * 255;
    uint frameRate = vats[float2(0, 0)].g * 255;

    //Get bounding box to scale the positions from 0-1 to it's actual value
    float bbMin = BytesToFloat(vats[float2(1, 0)]);
    float bbMax = BytesToFloat(vats[float2(2, 0)]);

    //Multiply time with framerate and loop if it hits the number of frame limit
    float animTime = ((OB_AliveTime * frameRate)% numFrames);
    float animTimeNext = (((OB_AliveTime * frameRate) + 1)% numFrames);
    float timeLerp = animTime - floor(animTime);

    //Sample vertexID from vertexcolors
    uint VTXId = BytesToUint(input.VxColor.rg);

    //Get the precomputed position value
    float2 timePosCurr = float2(VTXId, floor(animTime + 1));
    float2 timePosNext = float2(VTXId, floor(animTimeNext + 1));
    float3 lerpPos = lerp(vats[timePosCurr].xyz, vats[timePosNext].xyz, timeLerp);

    //And the normal value
    float2 timeNormCurr = float2(VTXId, floor(animTime + 1) + numFrames);
    float2 timeNormNext = float2(VTXId, floor(animTimeNext + 1) + numFrames);
    float3 lerpNorm = lerp(deriveNormalsFromPackage(vats[timeNormCurr]), deriveNormalsFromPackage(vats[timeNormNext]), timeLerp);

    //Remap the positions with the bounding box
    vtxPos.x -= Remap(0, 1, bbMin, bbMax, lerpPos.x);
    vtxPos.y += Remap(0, 1, bbMin, bbMax, lerpPos.y);
    vtxPos.z += Remap(0, 1, bbMin, bbMax, lerpPos.z);

    //Same with the normals
    vtxNorm.x -= Remap(0, 1, bbMin,  bbMax, lerpPos.x);
    vtxNorm.y += Remap(0, 1, bbMin,  bbMax, lerpPos.y);
    vtxNorm.z += Remap(0, 1, bbMin,  bbMax, lerpPos.z);

    float4 vertexWorldPosition = mul(OB_ToWorld, vtxPos);

    if (OB_isInstanced)
    {
        vertexWorldPosition = mul(input.World, mul(vtxPos, skinningMatrix));
    }

    const float4 vertexViewPosition = mul(FB_ToView, vertexWorldPosition);
    const float4 vertexProjectionPosition = mul(FB_ToProjection, vertexViewPosition);

    const float3x3 worldNormalRotation = (float3x3) OB_ToWorld;
    const float3x3 skinNormalRotation = (float3x3) skinningMatrix;
	
    result.ProjectedPosition = vertexProjectionPosition;
    result.WorldPosition = vertexWorldPosition;

    result.VxColor = input.VxColor;
    result.NormalTex = input.NormalTex;
    result.Roughness = input.Roughness;
    result.AO = input.AO;
    result.AlbedoUV = input.AlbedoUV;
    result.NormalUV = input.NormalUV;
    result.RoughnessUV = input.RoughnessUV;
    result.AOUV = input.AOUV;

    result.Tangent = mul(worldNormalRotation, mul(input.Tangent, skinNormalRotation));
    result.Binormal = mul(worldNormalRotation, mul(input.Binormal, skinNormalRotation));
    result.Normal = normalize(mul(worldNormalRotation, mul(vtxNorm, skinNormalRotation)));

    return result;
}
