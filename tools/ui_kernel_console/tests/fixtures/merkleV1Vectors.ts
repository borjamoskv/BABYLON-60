// Generado por tests/fixtures/generate_vectors.py. No editar a mano.

export const MERKLE_V1_SOURCE = "01_KISH_ENGINE/babylon60/attestation/merkle_b3.py de este repositorio, ejecutado con el paquete blake3 1.0.11";

export type LeafData = { readonly t: "utf8"; readonly v: string } | { readonly t: "lcg"; readonly seed: number; readonly len: number };

export const LEAF_HASHES: readonly { readonly data: LeafData; readonly hash: string }[] = [
  { data: { t: "utf8", v: "" }, hash: "3dfb055ec6ea7ab98ad0784e9678ea107819afab7e9d1021b160b00d740b07d4" }, // pragma: allowlist secret
  { data: { t: "utf8", v: "a" }, hash: "9094f0aaff51dd892d34b43d98b96b94bbddfcd4cd29632ce063ac9889b25ab0" }, // pragma: allowlist secret
  { data: { t: "utf8", v: "BISIM_LEAF_0" }, hash: "b2ad8bff1773c47dbef700a70ef8e41fbd652c55c4305fb8651713ba8ccd8033" }, // pragma: allowlist secret
  { data: { t: "lcg", seed: 1, len: 64 }, hash: "2f6f4a9c3faea538ed350dc5546c1ec9ee79ce2151fdcbe35c5cc064427f4ef2" }, // pragma: allowlist secret
  { data: { t: "lcg", seed: 2, len: 1024 }, hash: "4fdc09529ad5c813f278a77977d360f470f0ceb1900b0abb63c57d932bebff9f" }, // pragma: allowlist secret
  { data: { t: "lcg", seed: 3, len: 1025 }, hash: "f8ab003bdb3e1dae3548e7d829c9e7fa45fa72b38a1dba0f7825154f7d2ec07c" }, // pragma: allowlist secret
  { data: { t: "lcg", seed: 4, len: 5000 }, hash: "ab83990a59a930c62f2112bdbf200f875d9602fe0bc3062f96e6696564a3d3bf" }, // pragma: allowlist secret
];

/** Hijos izquierdo y derecho: bytes LCG de 32 bytes con las semillas indicadas. */
export const NODE_HASHES: readonly { readonly leftSeed: number; readonly rightSeed: number; readonly hash: string }[] = [
  { leftSeed: 10, rightSeed: 20, hash: "682d069fb7832c4ea2f9f88fdaf96cf5aab6187b30f18a1973c3bdccb169ba0a" }, // pragma: allowlist secret
  { leftSeed: 11, rightSeed: 21, hash: "d315bd469b1ecc2f932ff20f6265b3f0c064f37d80c2733b003b38ac0d825611" }, // pragma: allowlist secret
  { leftSeed: 12, rightSeed: 22, hash: "fac9a1a4d56f98e0dc46250d6d08305163124145fa27377835ca61477f8f9f8e" }, // pragma: allowlist secret
  { leftSeed: 13, rightSeed: 23, hash: "9f7f4aa99039cc0ab1eda0e513b6182c5e279c921d6e7f11944eb616b1182298" }, // pragma: allowlist secret
];

/** Hojas BISIM_LEAF_{i} para i en [0, n), como en tests/test_merkle_b3.py del repositorio. */
export const TEXT_ROOTS: readonly (readonly [n: number, root: string])[] = [
  [1, "b3:c6e1b1d10c5beac80db8bf3da3f18383753296f29023bc1506761eff7abcd765"], // pragma: allowlist secret
  [2, "b3:38aeba2b5dd306d8ea37a02ac14540f96ab7c05808122980419d25c3a2ba8541"], // pragma: allowlist secret
  [3, "b3:86d956f48efcd41c1dfd73416ec1c9de5ddf56e86119014a8e708a292a35f22c"], // pragma: allowlist secret
  [4, "b3:7b673774bceee21b5bd1534bb21307b3ce73c9fc13daaead296de806d13977c8"], // pragma: allowlist secret
  [5, "b3:7e380231c577f1fde7503cab0dc7bc52a12d217f9a93d243baa3a20e9ad9b7e5"], // pragma: allowlist secret
  [6, "b3:a2af86707aad10b14aa44e9da633e3d1c7ef51d2ea5e77cfba0742591ded2edf"], // pragma: allowlist secret
  [7, "b3:4304d495ed1699531fb5e5ccbc89ea5f5029507a5a9daced3d5bacfa67f4e448"], // pragma: allowlist secret
  [8, "b3:593641b03915cb51a71cea9758ec82bd027555331b6bef02e482ed0e0cd3eb43"], // pragma: allowlist secret
  [9, "b3:403b74feee6ed91508fed7ca63e3130dc21149b737e3ca037ee36d48560963ed"], // pragma: allowlist secret
  [10, "b3:940aaf8df06bb30fac1a497a5bc31d033326e7b5f893abd46c9d8d56a5963dec"], // pragma: allowlist secret
  [11, "b3:77bf95b2c67de4856206feae52500ff0532c329c6ba726f735a595d7f5d4c218"], // pragma: allowlist secret
  [12, "b3:7b3eb8f9541f5de350e430a6ffb2ba33c3407fa1da1a2539bb2516eddac24e22"], // pragma: allowlist secret
  [13, "b3:1637cef61bef974f9385e8536f58f1e227de0bf08cc7d7615a0543d843735837"], // pragma: allowlist secret
  [14, "b3:c972ca2a1fd802de2bdcbd71ba017c8b5aa1f176472b9dab0517252dd0c1bf93"], // pragma: allowlist secret
  [15, "b3:63890936a6f80972ea3468716516e17591a060bc573951a0fbce1b428697e832"], // pragma: allowlist secret
  [16, "b3:2c663a5ab72ed8cd7260ce8b54327ecadf320378128ef81f061dec0771593848"], // pragma: allowlist secret
  [17, "b3:4768a8d601caf0fe84d42924fbda5a701ecdfc4d732ea17aefdb4df64747fb9e"], // pragma: allowlist secret
  [31, "b3:b82cb23d74672f1253f862b9bf2e836879f0511319c08ea38e75cd4d2c794f01"], // pragma: allowlist secret
  [32, "b3:8cc4a81931104fc7e91d880b7d65791826ec0ee41c03497e5f82fdfcaf6314b8"], // pragma: allowlist secret
  [33, "b3:08505b6027e5aca597b4d97ef8c1a533f574e448c36da37385940eb476a56052"], // pragma: allowlist secret
  [64, "b3:63a81fa0dfeea6b72122bf0cfae7b24d722dca57f7d03ec3bfec94057edbd017"], // pragma: allowlist secret
  [65, "b3:1f4148168d48105e75dc236e2aceb4be78eae71008ff6ed64fac53c6ba8e633d"], // pragma: allowlist secret
  [100, "b3:d56fe71189aa741ccfe50072e579249435bce599ba01fc3d58923a2c12e431b4"], // pragma: allowlist secret
  [101, "b3:3e4aceee76b45a7a4c049a6c39bb55beaf1fb83c52644621274927dabda4e1f2"], // pragma: allowlist secret
  [257, "b3:02acf9036a798be04221504082462fafca66633df95a04d63affe3cf4a57ad35"], // pragma: allowlist secret
];

/** Hoja i: bytes LCG con semilla seed * 1000 + i y longitud (i * 37) % 200. */
export const BINARY_ROOTS: readonly { readonly n: number; readonly seed: number; readonly root: string }[] = [
  { n: 1, seed: 100, root: "b3:e1aeaa992770592a051a0ca763e48feabc7cb2642ed2a7525f6003bbb2524176" }, // pragma: allowlist secret
  { n: 2, seed: 101, root: "b3:de75c3378a58430ff2d4c98e620d258997703593628b5198534de6684834b162" }, // pragma: allowlist secret
  { n: 3, seed: 102, root: "b3:6f0498e1d1ad821ada949855d0c0fba82e9b1da18437cace39938fa48ac43e74" }, // pragma: allowlist secret
  { n: 5, seed: 103, root: "b3:6e569c0b1f4bb78a73bbb668cf23c29304abb0687fa9306464de656facbf7c6b" }, // pragma: allowlist secret
  { n: 6, seed: 104, root: "b3:2edf789666fc9f01311c7c2f9765d72a9efc3d00473b710a6d4fd77a507e2a94" }, // pragma: allowlist secret
  { n: 7, seed: 105, root: "b3:b0ba1c2e4deaad696e2214bed54acd342390ea2523941c78810246f3f19db4fa" }, // pragma: allowlist secret
  { n: 9, seed: 106, root: "b3:3333cce09168a01aedf748906fa5a001f6f734a24dbea6c42573e0766c998df4" }, // pragma: allowlist secret
];
