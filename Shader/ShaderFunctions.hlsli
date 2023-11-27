#Copyright Tim Lindberg

uint BytesToUint(float2 bytes)
{
    uint MSB = uint(bytes.x * 255);
    uint LSB = uint(bytes.y * 255);
    uint result = MSB << 8;
    return result | LSB;
}

float BytesToFloat(float4 bytes)
{
    uint byte_1 = uint(bytes.w * 255);
    uint byte_2 = uint(bytes.z * 255);
    uint byte_3 = uint(bytes.y * 255);
    uint byte_4 = uint(bytes.x * 255);
    
    uint uintResult = byte_1 << 8;
    uintResult = uintResult | byte_2;
    uintResult = uintResult << 8;
    uintResult = uintResult | byte_3;
    uintResult = uintResult << 8;
    uintResult = uintResult | byte_4;
    
    return asfloat(uintResult);
}

float3 deriveNormalsFromPackage(float4 lePackage)
{
    float3 normalXYz = 0;
    uint MSB = 0;
    uint LSB = 0;
    uint result = 0;
    
    MSB = uint(lePackage.x * 255);
    LSB = uint(lePackage.y * 255);
    result = MSB << 8;
    normalXYz.x = Remap(0, 65535, -1, 1, uint(result | LSB));
 
    MSB = uint(lePackage.z * 255);
    LSB = uint(lePackage.w * 255);
    result = MSB << 8;
    normalXYz.y = Remap(0, 65535, -1, 1, uint(result | LSB));
    
    normalXYz.z = sqrt(normalize(dot(normalXYz.xy, normalXYz.xy)));
    return normalize(normalXYz);
}
